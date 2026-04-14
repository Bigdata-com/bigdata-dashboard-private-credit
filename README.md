# Private Credit Stress Analyzer

Thematic signal search over lenders and borrowers using the [Bigdata API](https://bigdata.com). The pipeline scores each entity (terms power versus stress), then writes a ranked Excel workbook and a standalone HTML dashboard.

Requires Python 3.11+ and [uv](https://github.com/astral-sh/uv).

Background on the workflow and participants: [docs/private_credit_business_process.md](docs/private_credit_business_process.md).

This project is a technical demo showcasing Bigdata capabilities. It is not investment advice.

## Quick start

```bash
uv sync
cp .env.example .env   # set BIGDATA_API_KEY
uv run python main.py
```

## CLI

```bash
uv run python main.py
uv run python main.py --skip-search
uv run python main.py --clear-cache
uv run python main.py --layer lender
uv run python main.py --layer borrower
uv run python main.py --entity "Blue Owl Capital"
uv run python main.py --max-workers 3
```

Local cache lives under `.cache/` (search JSON, scoring snapshots used by the audit tab, and `scores.csv`). Use `--clear-cache` after you change entities, topics, or search settings, or delete `.cache/` and run again. The HTML audit reads `.cache/scoring_audit/`; run scoring before generating reports if you use `src/reporter.py` alone.

## Pipeline stages

| Stage | Command |
|-------|---------|
| Search | `uv run python src/search.py` |
| Score | `uv run python src/scorer.py` |
| Report | `uv run python src/reporter.py` |

## Layout

| Path | Purpose |
|------|---------|
| `dist/` | Static site (`index.html`), Excel export, `.nojekyll` |
| `.cache/` | Raw search results, `scoring_audit/` snapshots, `scores.csv` |
| `docs/` | Notes; see `docs/README.md` |
| `config/entities.py` | Lender and borrower universe |
| `config/topics.py` | Search topics and polarity |

## Publishing (GitHub Pages)

The workflow is defined in [`.github/workflows/pages.yml`](.github/workflows/pages.yml). In the repository settings, set Pages to build from GitHub Actions. Adjust the workflow or branch as needed for your fork.

## Deploy (Fly.io)

Apps for this repo should live under the Fly.io organization **`ravenpack-internation-slu`**. You need a Fly account that is a member of that org.

1. Install [flyctl](https://fly.io/docs/hands-on/install-flyctl/) and sign in:
   ```bash
   fly auth login
   ```
2. Confirm the org exists and you have access:
   ```bash
   fly orgs show rave****
   ```
3. From the repository root (where `fly.toml` and `Dockerfile` are), **first-time setup** — create the app in that org (pick a unique name if `private-credit-stress` is taken):
   ```bash
   fly launch --org rave**** --no-deploy
   ```
   Align `app` in `fly.toml` with the name you chose, or accept the generated config.
4. **Deploy:**
   ```bash
   fly deploy
   ```
   The app stays under the org it was created in; later deploys do not need `--org` unless you use `fly apps create` / `fly launch` again.
5. **Single machine:** `fly.toml` sets **1024 MiB** RAM and **`min_machines_running = 1`**. If the app was ever scaled up, run **`fly scale count 1`** so only one machine runs.
6. Open the app: `fly open` or the URL printed after deploy.

Health checks use **`GET /health`** (no API key). The dashboard HTML is served at **`GET /`**; API routes require the user’s Bigdata key via **`X-API-KEY`**.

## Scoring

```
terms_power_score = positive_count / (positive_count + negative_count + 1) * 100
stress_score = 100 - terms_power_score
```

Lenders rank higher when `terms_power_score` is high (more weight on positive themes). Borrowers rank higher when `stress_score` is high (more weight on distress-oriented topics).

Counts are ratios of topic-aligned mentions (with entity name in the returned text), not raw article volume. The distress radar reuses the same per-topic counts as the heatmap but highlights negative themes.

## Project tree

```
├── main.py
├── pyproject.toml
├── .env.example
├── config/
│   ├── entities.py
│   ├── paths.py
│   └── topics.py
├── docs/
├── .github/workflows/pages.yml
├── .cache/          # local only
├── dist/
└── src/
    ├── search.py
    ├── scorer.py
    ├── reporter.py
    └── utils.py
```

