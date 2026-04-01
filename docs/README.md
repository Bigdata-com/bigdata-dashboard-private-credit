# Documentation

Human-readable reference material for the Private Credit Stress Analyzer.

| Document | Description |
|----------|-------------|
| [private_credit_business_process.md](private_credit_business_process.md) | Business context: lenders, borrowers, banks, scoring narrative |

Build artifacts **do not** belong here. The pipeline writes:

- **`dist/`** — `index.html`, `private_credit_stress.xlsx` (GitHub Pages)
- **`.cache/`** — `raw/*.json`, `scores.csv` (local only, gitignored)

If you have leftover `docs/raw/`, `docs/index.html`, or `docs/scores.csv` from an older layout, delete them or move JSON to `.cache/raw/` to reuse cache without re-searching.
