"""Application logging: file (log/app.log) + stderr for the FastAPI server."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_LOG_CONFIGURED = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "log"
APP_LOG_FILE = LOG_DIR / "app.log"


def configure_app_logging(level: int = logging.INFO) -> None:
    """Attach file + stream handlers once (safe across uvicorn reload)."""
    global _LOG_CONFIGURED
    if _LOG_CONFIGURED:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(APP_LOG_FILE, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    # Quieter third-party noise at INFO
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    _LOG_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
