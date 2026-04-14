"""Private Credit Stress Analyzer — FastAPI Web Server.

Serves the pre-generated dashboard as the default view and provides API
endpoints for Bigdata company lookup and on-demand pipeline execution with
the user's own API key.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from starlette.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.paths import EXCEL_OUTPUT, HTML_INDEX
from src.app_logging import APP_LOG_FILE, configure_app_logging

configure_app_logging()
log = logging.getLogger("server")

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Private Credit Stress Analyzer", docs_url=None, redoc_url=None)

# Same-origin dashboard + API: browsers do not require CORS for fetches to this host.
# Wildcard + no credentials avoids invalid * + credentials pairs if anything is cross-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

_AUTH_ERROR = {
    "error": "API key required",
    "message": "Please provide your Bigdata API key via the X-API-KEY request header",
}


async def require_api_key(
    x_api_key: str | None = Header(None, alias="X-API-KEY"),
) -> str:
    if not x_api_key or not x_api_key.strip():
        raise HTTPException(status_code=401, detail=_AUTH_ERROR)
    return x_api_key.strip()


@app.middleware("http")
async def enforce_bigdata_api_key(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Require X-API-KEY on every request except HTML shell, health, and CORS preflight."""
    if request.method == "OPTIONS":
        return await call_next(request)
    path = request.url.path
    if path == "/" and request.method == "GET":
        return await call_next(request)
    if path == "/health" and request.method == "GET":
        return await call_next(request)
    raw = request.headers.get("X-API-KEY") or request.headers.get("x-api-key")
    if not raw or not str(raw).strip():
        return JSONResponse(status_code=401, content=_AUTH_ERROR)
    return await call_next(request)


@app.middleware("http")
async def log_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    start = time.perf_counter()
    client = request.client.host if request.client else "?"
    path = request.url.path
    log.info("HTTP %s %s client=%s", request.method, path, client)
    try:
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        log.info(
            "HTTP %s %s -> %s in %.1fms",
            request.method,
            path,
            response.status_code,
            elapsed_ms,
        )
        return response
    except Exception:
        log.exception("HTTP %s %s failed", request.method, path)
        raise


# ---------------------------------------------------------------------------
# Pipeline job store (in-memory, auto-cleaned)
# ---------------------------------------------------------------------------

pipeline_jobs: dict[str, dict[str, Any]] = {}
JOB_TTL_SECONDS = 3600


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------


class CompanyLookupRequest(BaseModel):
    names: list[str] = Field(..., min_length=1, max_length=50)
    layer: str = Field(..., pattern=r"^(lender|borrower)$")


class PipelineEntity(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    rp_entity_id: str | None = None
    layer: str = Field(..., pattern=r"^(lender|borrower)$")
    ticker: str | None = None


class PipelineRunRequest(BaseModel):
    entities: list[PipelineEntity] = Field(..., min_length=1, max_length=30)


# ---------------------------------------------------------------------------
# Static / page routes
# ---------------------------------------------------------------------------


@app.get("/")
async def index() -> HTMLResponse:
    if HTML_INDEX.exists():
        return HTMLResponse(HTML_INDEX.read_text())
    return HTMLResponse(
        "<h1>Dashboard not generated yet. Run the pipeline first.</h1>",
        status_code=503,
    )


@app.get("/health")
async def health() -> dict[str, str]:
    """Public probe for load balancers (e.g. Fly.io); no sensitive data."""
    return {"status": "ok"}


@app.get("/api/config")
async def config(_api_key: str = Depends(require_api_key)) -> dict[str, Any]:
    """Requires X-API-KEY (same as other API routes); key is not stored server-side."""
    return {"bigdata_api_key_configured": False}


@app.get("/download/excel")
async def download_excel(
    _api_key: str = Depends(require_api_key),
) -> FileResponse:
    if EXCEL_OUTPUT.exists():
        return FileResponse(
            str(EXCEL_OUTPUT),
            filename="private_credit_stress.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    raise HTTPException(404, detail="Excel report not found")


# ---------------------------------------------------------------------------
# Company lookup (Bigdata Python client — same path as MCP find_companies)
# ---------------------------------------------------------------------------


def _company_to_match_dict(c: Any) -> dict[str, Any]:
    """Shape matches frontend / MCP find_companies expectations."""
    return {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "listing_values": c.listing_values,
        "type": c.company_type,
        "country": c.country,
        "sector": c.sector,
        "industry_group": c.industry_group,
        "industry": c.industry,
        "webpage": c.webpage,
    }


def _organization_to_match_dict(o: Any) -> dict[str, Any]:
    return {
        "id": o.id,
        "name": o.name,
        "description": o.description,
        "listing_values": None,
        "type": o.organization_type,
        "country": o.country,
        "sector": None,
        "industry_group": None,
        "industry": None,
        "webpage": None,
    }


def _sync_company_lookup(api_key: str, names: list[str], layer: str) -> list[dict[str, Any]]:
    """Blocking KG lookup using official bigdata_client (avoids wrong REST URLs / 403)."""
    from bigdata_client import Bigdata
    from bigdata_client.models.entities import Company, Organization

    bd = Bigdata(api_key=api_key)
    kg = bd.knowledge_graph
    results: list[dict[str, Any]] = []

    for name in names:
        name = name.strip()
        if not name:
            continue
        matches: list[dict[str, Any]] = []
        err: str | None = None
        try:
            log.info("company_lookup KG find_companies query=%r layer=%s", name, layer)
            companies = kg.find_companies(name, limit=10)
            for c in companies:
                if isinstance(c, Company):
                    matches.append(_company_to_match_dict(c))
            if not matches:
                log.info(
                    "company_lookup no companies for %r; trying find_organizations",
                    name,
                )
                orgs = kg.find_organizations(name, limit=10)
                for o in orgs:
                    if isinstance(o, Organization):
                        matches.append(_organization_to_match_dict(o))
            log.info(
                "company_lookup query=%r -> %d match(es) (top 5 returned)",
                name,
                len(matches),
            )
        except Exception as exc:
            err = str(exc)
            log.exception("company_lookup failed query=%r: %s", name, exc)

        row: dict[str, Any] = {"input_name": name, "matches": matches[:5]}
        if err:
            row["error"] = err
        if not matches and not err:
            row["error"] = "No matching company or organization in knowledge graph"
            log.warning("company_lookup query=%r -> zero matches", name)
        results.append(row)

    return results


@app.post("/api/company-lookup")
@limiter.limit("30/minute")
async def company_lookup(
    request: Request,
    body: CompanyLookupRequest,
    api_key: str = Depends(require_api_key),
) -> dict[str, Any]:
    names = [n.strip() for n in body.names if n and str(n).strip()]
    log.info(
        "POST /api/company-lookup layer=%s names=%d (logging to %s)",
        body.layer,
        len(names),
        APP_LOG_FILE,
    )
    results = await asyncio.to_thread(_sync_company_lookup, api_key, names, body.layer)
    return {"results": results}


# ---------------------------------------------------------------------------
# Async pipeline execution
# ---------------------------------------------------------------------------


def _run_pipeline_thread(
    job_id: str,
    entities_data: list[dict[str, Any]],
    api_key: str,
) -> None:
    """Execute search -> score -> prepare in a background thread."""
    job = pipeline_jobs[job_id]
    _layer = entities_data[0].get("layer") if entities_data else "?"
    log.info(
        "pipeline job_id=%s started entity_count=%d layer=%s",
        job_id,
        len(entities_data),
        _layer,
    )
    try:
        from config.entities import EntityDict
        from src.reporter import _prepare_layer_data
        from src.scorer import compute_scores
        from src.search import run_all_searches

        entities: list[EntityDict] = [
            {"name": e["name"], "ticker": e.get("ticker"), "layer": e["layer"]}
            for e in entities_data
        ]

        layer = entities[0]["layer"]
        total = len(entities)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            raw_dir = tmp / "raw"
            audit_dir = tmp / "scoring_audit"
            scores_csv = tmp / "scores.csv"

            def _progress(msg: str) -> None:
                job["progress"] = msg

            job["progress"] = f"Searching {total} entities..."
            run_all_searches(
                entities=entities,
                api_key=api_key,
                cache_dir=raw_dir,
                max_workers=5,
                progress_callback=_progress,
            )

            job["progress"] = "Computing scores..."
            df = compute_scores(
                entities=entities,
                raw_dir=raw_dir,
                audit_dir=audit_dir,
                scores_csv=scores_csv,
            )

            job["progress"] = "Preparing dashboard data..."
            layer_data = _prepare_layer_data(
                df,
                layer,
                entities=entities,
                audit_dir=audit_dir,
            )

            job["data"] = layer_data
            job["status"] = "complete"
            job["progress"] = "Done"
            log.info("pipeline job_id=%s completed successfully", job_id)
    except Exception as exc:
        job["status"] = "failed"
        job["error"] = str(exc)
        job["progress"] = f"Failed: {exc}"
        log.exception("pipeline job_id=%s failed: %s", job_id, exc)


@app.post("/api/pipeline/run")
@limiter.limit("5/minute")
async def run_pipeline(
    request: Request,
    body: PipelineRunRequest,
    api_key: str = Depends(require_api_key),
) -> dict[str, str]:
    job_id = str(uuid.uuid4())
    entities_data = [e.model_dump() for e in body.entities]
    log.info(
        "POST /api/pipeline/run job_id=%s entities=%d",
        job_id,
        len(entities_data),
    )

    pipeline_jobs[job_id] = {
        "status": "running",
        "progress": "Starting...",
        "started_at": time.time(),
        "data": None,
        "error": None,
    }

    thread = threading.Thread(
        target=_run_pipeline_thread,
        args=(job_id, entities_data, api_key),
        daemon=True,
    )
    thread.start()

    return {"job_id": job_id, "status": "running"}


@app.get("/api/pipeline/status/{job_id}")
async def pipeline_status(
    job_id: str,
    _api_key: str = Depends(require_api_key),
) -> dict[str, Any]:
    job = pipeline_jobs.get(job_id)
    if not job:
        raise HTTPException(404, detail="Job not found")
    elapsed = (time.time() - job["started_at"]) * 1000
    return {
        "status": job["status"],
        "progress": job["progress"],
        "elapsed_ms": round(elapsed),
        "error": job.get("error"),
    }


@app.get("/api/pipeline/data/{job_id}", response_model=None)
async def pipeline_data(
    job_id: str,
    _api_key: str = Depends(require_api_key),
) -> JSONResponse:
    job = pipeline_jobs.get(job_id)
    if not job:
        raise HTTPException(404, detail="Job not found")
    if job["status"] != "complete":
        raise HTTPException(400, detail="Pipeline not complete yet")
    return JSONResponse(content=job["data"])


# ---------------------------------------------------------------------------
# Periodic job cleanup
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def start_cleanup() -> None:
    configure_app_logging()
    log.info("Server startup — app log file: %s", APP_LOG_FILE)

    async def _cleanup_loop() -> None:
        while True:
            await asyncio.sleep(300)
            now = time.time()
            expired = [
                jid
                for jid, j in pipeline_jobs.items()
                if now - j["started_at"] > JOB_TTL_SECONDS
            ]
            for jid in expired:
                pipeline_jobs.pop(jid, None)
                log.debug("pipeline job_id=%s evicted (TTL)", jid)
            if expired:
                log.info("Cleaned %d expired pipeline job(s)", len(expired))

    asyncio.create_task(_cleanup_loop())


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
