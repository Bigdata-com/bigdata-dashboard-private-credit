from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv
from rich.table import Table

from bigdata_client import Bigdata
from bigdata_client.daterange import AbsoluteDateRange
from bigdata_client.query import SentimentRange, Similarity
from bigdata_research_tools.search.search import run_search

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.entities import ALL_ENTITIES, EntityDict
from config.paths import RAW_CACHE_DIR
from config.topics import TOPICS, TopicDict
from src.utils import (
    console,
    format_elapsed,
    retry_with_backoff,
    sanitize_filename,
    setup_logger,
)

logger = setup_logger(__name__)

RAW_OUTPUT_DIR = RAW_CACHE_DIR

# Single source of truth for Bigdata search date filter (used in search + dashboard methodology)
SEARCH_START_DATE = datetime(2025, 1, 1)
SEARCH_END_DATE = datetime(2026, 3, 30)  # end of current year; no future dates
SEARCH_DATE_LABEL = "Jan 1, 2025 – Mar 30, 2026"


def _get_bigdata_client(api_key: str | None = None) -> Bigdata:
    if api_key:
        return Bigdata(api_key=api_key)
    load_dotenv()
    return Bigdata()


def _build_jobs(
    entities: list[EntityDict],
    topics: list[TopicDict],
    skip_cached: bool = True,
    cache_dir: Path | None = None,
) -> list[tuple[EntityDict, TopicDict]]:
    """Build (entity, topic) pairs, filtering by applies_to and optionally skipping cached."""
    jobs: list[tuple[EntityDict, TopicDict]] = []
    for entity in entities:
        layer = entity["layer"]
        for topic in topics:
            if layer not in topic["applies_to"]:
                continue

            if skip_cached:
                filename = _result_path(entity, topic, cache_dir=cache_dir)
                if filename.exists():
                    continue

            jobs.append((entity, topic))
    return jobs


def _result_path(
    entity: EntityDict, topic: TopicDict, cache_dir: Path | None = None,
) -> Path:
    entity_slug = sanitize_filename(str(entity["name"]))
    topic_slug = sanitize_filename(str(topic["topic_name"]))
    base = cache_dir if cache_dir is not None else RAW_OUTPUT_DIR
    return base / f"{entity_slug}_{topic_slug}.json"


def _sentiment_filter_for_topic_polarity(polarity: str) -> SentimentRange | None:
    """Map topic polarity to the SDK sentiment expression (aligned with REST filters.sentiment)."""
    p = str(polarity).strip().lower()
    if p == "positive":
        # Strictly above neutral to mirror categorical "positive" filter
        return SentimentRange((1e-6, 1.0))
    if p == "negative":
        return SentimentRange((-1.0, -1e-6))
    return None


def _reformulate_queries(query_text: str, entity_name: str) -> list[str]:
    """Build multiple query variants for reformulation to improve recall.

    Returns the original query plus 2 shorter variants (entity-focused and key-term).
    """
    parts = query_text.replace("{company}", entity_name).strip().split()
    if len(parts) <= 6:
        return [query_text.replace("{company}", entity_name)]
    # Original full query (with {company} already replaced by caller)
    full = query_text.replace("{company}", entity_name)
    variants = [full]
    # Entity + first half of topic (after entity)
    mid = min(6, len(parts) // 2)
    variants.append(" ".join(parts[:mid]))
    # Entity + last half (key terms)
    if len(parts) > mid:
        variants.append(" ".join(parts[mid:]))
    return list(dict.fromkeys(variants))  # dedupe order-preserving


@retry_with_backoff(max_retries=3, base_delay=2.0)
def _run_single_search(
    bigdata: Bigdata,
    entity: EntityDict,
    topic: TopicDict,
    cache_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute a single (entity, topic) search with query reformulation; save merged result."""
    query_text = str(topic["topic_text"]).replace("{company}", str(entity["name"]))
    entity_name = str(entity["name"])
    query_variants = _reformulate_queries(str(topic["topic_text"]), entity_name)
    start_ms = time.time() * 1000

    sentiment_q = _sentiment_filter_for_topic_polarity(str(topic["polarity"]))
    queries = [
        (Similarity(q) & sentiment_q) if sentiment_q is not None else Similarity(q)
        for q in query_variants
    ]
    search_results = run_search(
        queries,
        date_ranges=AbsoluteDateRange(SEARCH_START_DATE, SEARCH_END_DATE),
        bigdata=bigdata,
        limit=20,
        workflow_name="PrivateCreditStressAnalyzer",
    )

    elapsed_ms = time.time() * 1000 - start_ms

    seen: set[str] = set()
    results_list: list[dict[str, Any]] = []
    for batch in search_results:
        for doc in batch:
            content = "".join(chunk.text for chunk in doc.chunks)
            key = (doc.headline or "") + "|" + (doc.url or "")
            if key in seen:
                continue
            seen.add(key)
            results_list.append({
                "headline": doc.headline,
                "content": content,
                "timestamp": str(doc.timestamp) if doc.timestamp else None,
                "url": doc.url if hasattr(doc, "url") else None,
            })
    results_list = results_list[:50]

    result_payload: dict[str, Any] = {
        "entity_name": entity["name"],
        "entity_ticker": entity["ticker"],
        "entity_layer": entity["layer"],
        "topic_name": topic["topic_name"],
        "topic_polarity": topic["polarity"],
        "query_text": query_text,
        "n_results": len(results_list),
        "elapsed_ms": round(elapsed_ms, 1),
        "results": results_list,
    }

    output_path = _result_path(entity, topic, cache_dir=cache_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result_payload, indent=2, default=str))

    logger.info(
        "%s | %s | %d results | %s",
        entity["name"],
        topic["topic_name"],
        len(results_list),
        format_elapsed(elapsed_ms),
    )
    return result_payload


def run_all_searches(
    entities: list[EntityDict] | None = None,
    layer_filter: str | None = None,
    entity_filter: str | None = None,
    max_workers: int = 10,
    api_key: str | None = None,
    cache_dir: Path | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> dict[str, int]:
    """Run all (entity x topic) searches in parallel.

    Returns summary dict with total, success, skipped, failed counts.
    """
    target_entities = entities or ALL_ENTITIES

    if layer_filter:
        target_entities = [e for e in target_entities if e["layer"] == layer_filter]

    if entity_filter:
        target_entities = [e for e in target_entities if e["name"] == entity_filter]

    all_possible = _build_jobs(target_entities, TOPICS, skip_cached=False, cache_dir=cache_dir)
    jobs = _build_jobs(target_entities, TOPICS, skip_cached=True, cache_dir=cache_dir)

    skipped = len(all_possible) - len(jobs)
    success = 0
    failed = 0

    console.rule("[bold cyan]Private Credit Stress Analyzer — Search Phase")
    console.print(
        f"Total jobs: {len(all_possible)} | To run: {len(jobs)} | Cached: {skipped}"
    )

    if not jobs:
        console.print("[green]All results cached. Skipping search phase.[/green]")
        return {"total": len(all_possible), "success": 0, "skipped": skipped, "failed": 0}

    bigdata = _get_bigdata_client(api_key=api_key)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _run_single_search, bigdata, entity, topic, cache_dir,
            ): (entity, topic)
            for entity, topic in jobs
        }

        for future in as_completed(futures):
            entity, topic = futures[future]
            try:
                future.result()
                success += 1
                if progress_callback:
                    progress_callback(
                        f"Searched {success + failed}/{len(jobs)}: {entity['name']} × {topic['topic_name']}"
                    )
            except Exception as exc:
                failed += 1
                logger.error(
                    "FAILED: %s | %s | %s",
                    entity["name"],
                    topic["topic_name"],
                    exc,
                )

    summary_table = Table(title="Search Summary")
    summary_table.add_column("Metric", style="bold")
    summary_table.add_column("Count", justify="right")
    summary_table.add_row("Total Jobs", str(len(all_possible)))
    summary_table.add_row("Success", f"[green]{success}[/green]")
    summary_table.add_row("Cached (skipped)", f"[yellow]{skipped}[/yellow]")
    summary_table.add_row("Failed", f"[red]{failed}[/red]")
    console.print(summary_table)

    return {"total": len(all_possible), "success": success, "skipped": skipped, "failed": failed}


if __name__ == "__main__":
    run_all_searches()
