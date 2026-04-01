# Private Credit Stress Analyzer

Analyze private credit market stress by running thematic signal searches across three entity layers — **Lenders**, **Borrowers**, and **Banks** — using the [Bigdata API](https://bigdata.com). The system scores each entity on a **Terms Power Score** and a **Stress Score**, then outputs a ranked Excel report with an interactive HTML dashboard.

Long-form business context: see **[docs/private_credit_business_process.md](docs/private_credit_business_process.md)**.

## Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Set your API key
cp .env.example .env
# Edit .env and add your BIGDATA_API_KEY

# 3. Run the full pipeline
uv run python main.py
```

## CLI Options

```bash
uv run python main.py                          # Full run (all entities, all layers)
uv run python main.py --skip-search            # Use cached results, regenerate scores + reports
uv run python main.py --clear-cache            # Clear raw cache, then run full pipeline (fresh search)
uv run python main.py --layer lender           # Run only lender layer
uv run python main.py --entity "Blue Owl Capital"  # Single entity
uv run python main.py --max-workers 3          # Control parallelism
```

## Clear cache

Search JSON and scores live under **`.cache/`** (gitignored):

| Path | Contents |
|------|----------|
| `.cache/raw/*.json` | One file per (entity × topic) Bigdata search |
| `.cache/scores.csv` | Intermediate scores for reporting |

**Option 1 — CLI (recommended)**

```bash
uv run python main.py --clear-cache
```

**Option 2 — Manual**

```bash
rm -rf .cache/raw/*.json
# or: rm -rf .cache
uv run python main.py
```

Use `--clear-cache` when you change topics/entities, the search date range, or query logic.

## Pipeline stages

| Stage | Command | Description |
|-------|---------|-------------|
| **Search** | `uv run python src/search.py` | Run (entity × topic) searches via Bigdata, cache as JSON |
| **Score** | `uv run python src/scorer.py` | Aggregate mention counts into Terms Power and Stress scores |
| **Report** | `uv run python src/reporter.py` | Generate Excel workbook + standalone HTML dashboard |

## Folders

| Folder | Role | Git |
|--------|------|-----|
| **`dist/`** | GitHub Pages: `index.html`, `private_credit_stress.xlsx`, `.nojekyll` | Commit published files |
| **`.cache/`** | Pipeline cache: `raw/*.json`, `scores.csv` | Ignored |
| **`docs/`** | Markdown documentation only (see `docs/README.md`) | Commit `.md` files |

## Publish `dist/` on GitHub Pages

Use **GitHub Actions** (`.github/workflows/pages.yml`) so pushes deploy the committed **`dist/`** tree.

1. **Settings → Pages → Source:** **GitHub Actions**.
2. After each local run:

```bash
uv run python main.py   # writes .cache/* and dist/*
git add dist/index.html dist/private_credit_stress.xlsx dist/.nojekyll
git commit -m "Update dashboard and Excel"
git push origin main
```

Site URL: **Settings → Pages** (often `https://<user>.github.io/<repo>/`).

## Entity layers

- **Lenders** (20): `config/entities.py` — `LENDERS`
- **Borrowers**: `config/entities.py` — `BORROWERS`
- **Banks** (5): in `config/entities.py`; excluded while `INCLUDE_BANKS_LAYER` is `False`

## Scoring

```
terms_power_score = positive_count / (positive_count + negative_count + 1) × 100
stress_score = 100 − terms_power_score
```

- **Lenders** ranked by `terms_power_score` (high = strong)
- **Borrowers** ranked by `stress_score` (high = distressed)
- **Banks** ranked by net position: `market_share_gain − credit_pullback`

**Why stress can be high with “low” heatmap numbers:** The score is a *ratio* of positive vs negative topic counts, not raw volume. The **Distress radar** and **Signal heatmap** share the same per-topic counts; the radar shows only negative (distress) topics.

## Project structure

```
bigdata-dashboard-private-credit/
├── main.py
├── pyproject.toml
├── .env.example
├── config/
│   ├── entities.py
│   ├── paths.py             # dist/, .cache/, docs/ layout
│   └── topics.py
├── docs/                    # Markdown docs (committed)
│   ├── README.md
│   └── private_credit_business_process.md
├── .github/workflows/pages.yml
├── .cache/                  # gitignored — created by pipeline
├── dist/                    # commit after run — GitHub Pages
└── src/
    ├── search.py
    ├── scorer.py
    ├── reporter.py
    └── utils.py
```

## Cleaning up an old `docs/` layout

If your repo still has **generated** files under `docs/`:

| If you see… | Action |
|-------------|--------|
| `docs/raw/*.json` | Move to `.cache/raw/` to keep cache, or delete and re-run search |
| `docs/index.html` | Delete — use `dist/index.html` |
| `docs/scores.csv` | Delete — use `.cache/scores.csv` |
| `docs/private_credit_business_process.md` | **Keep** — real documentation |
| `docs/README.md` | **Keep** — documentation index |

`.gitignore` ignores common stray artifacts under `docs/` so they are not committed by mistake.
