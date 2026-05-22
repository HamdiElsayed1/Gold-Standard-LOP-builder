"""Load Fleur `src/.env` — single source of truth for the env file path."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent / ".env"


def load_app_env() -> None:
    """Load API keys and gateway URLs from `.env` in this directory (beside `app.py`)."""
    load_dotenv(_ENV_PATH)
