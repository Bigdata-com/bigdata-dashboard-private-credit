# Private Credit Stress Analyzer

Thematic signal search over **lenders** and **borrowers** using the [Bigdata API](https://bigdata.com). The pipeline scores each entity (terms power vs stress), then produces a ranked Excel workbook and a standalone HTML dashboard.

**Prerequisites:** Python 3.11+ and [uv](https://github.com/astral-sh/uv).

Background on the private credit workflow and participants: [docs/private_credit_business_process.md](docs/private_credit_business_process.md).

*This project is a technical demo for research and exploration; it is not investment advice.*

## Quick start

```bash
uv sync
cp .env.example .env   # add BIGDATA_API_KEY
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

Search results and scores are cached under **`.cache/`** (gitignored). Use `--clear-cache` when you change entities, topics, or search parameters—or remove `.cache` and run again.

## Pipeline

| Stage | Command |
|-------|---------|
| Search | `uv run python src/search.py` |
| Score | `uv run python src/scorer.py` |
| Report | `uv run python src/reporter.py` |

## Repository layout

| Path | Purpose |
|------|---------|
| `dist/` | GitHub Pages assets: `index.html`, `private_credit_stress.xlsx`, `.nojekyll` — commit after a full run when publishing |
| `.cache/` | Local scratch: `raw/*.json`, `scores.csv` — not committed |
| `docs/` | Markdown notes (`docs/README.md` indexes them) |
| `config/entities.py` | Lender and borrower universes |
| `config/topics.py` | Search topics and polarity |

## GitHub Pages

Workflow: [`.github/workflows/pages.yml`](.github/workflows/pages.yml). In the repo, **Settings → Pages → Build and deployment → Source:** choose **GitHub Actions**.

After generating output:

```bash
uv run python main.py
git add dist/index.html dist/private_credit_stress.xlsx dist/.nojekyll
git commit -m "Update dashboard and Excel"
git push
```

The live URL appears under **Settings → Pages** (often `https://<user>.github.io/<repo>/`).

## Scoring

```
terms_power_score = positive_count / (positive_count + negative_count + 1) × 100
stress_score = 100 − terms_power_score
```

- **Lenders** — ranked higher when `terms_power_score` is high (stronger narrative on positive themes).
- **Borrowers** — ranked higher when `stress_score` is high (more weight on distress-oriented topics).

Scores are **ratios of topic mentions**, not raw news volume. The dashboard **Distress radar** uses the same per-topic counts as the heatmap but emphasizes negative (distress) themes.

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
├── .cache/          # created locally; gitignored
├── dist/            # publishable site + workbook
└── src/
    ├── search.py
    ├── scorer.py
    ├── reporter.py
    └── utils.py
```

If you still have old generated files under `docs/` (`raw/`, `index.html`, `scores.csv`), remove them—the pipeline uses `.cache/` and `dist/` instead. See `docs/README.md`.
