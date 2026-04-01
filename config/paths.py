"""Path layout: dist/ (publish), docs/ (human docs), .cache/ (local pipeline cache, gitignored)."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# Published for GitHub Pages — commit after running the pipeline.
DIST_DIR: Path = PROJECT_ROOT / "dist"
HTML_INDEX: Path = DIST_DIR / "index.html"
EXCEL_OUTPUT: Path = DIST_DIR / "private_credit_stress.xlsx"

# Local cache only (gitignored): search JSON + intermediate scores.
CACHE_DIR: Path = PROJECT_ROOT / ".cache"
RAW_CACHE_DIR: Path = CACHE_DIR / "raw"
SCORES_CSV: Path = CACHE_DIR / "scores.csv"
