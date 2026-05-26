"""
src/database/config.py

Environment-aware Supabase client.

Priority order for credentials:
  1. Environment variables  (production / Docker / FastAPI)
  2. Streamlit secrets      (local dev with streamlit run)

This means the same file works in both contexts with zero changes.
"""

import os
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)


def _resolve(key: str) -> str:
    """
    Resolve a config value from env vars first, Streamlit secrets second.
    Raises a clear RuntimeError if neither source has the value.
    """
    # 1. Environment variable (works in FastAPI, Docker, CI/CD)
    value = os.environ.get(key)
    if value:
        return value

    # 2. Streamlit secrets (works during `streamlit run`)
    try:
        import streamlit as st
        value = st.secrets.get(key)
        if value:
            return value
    except Exception:
        # Streamlit is not running — that's fine, we'll fall through
        pass

    raise RuntimeError(
        f"Missing required config: '{key}'. "
        f"Set it as an environment variable or in .streamlit/secrets.toml"
    )


def _create_supabase_client() -> Client:
    url = _resolve("SUPABASE_URL")
    key = _resolve("SUPABASE_KEY")
    logger.info("Supabase client initialised (url=%s...)", url[:30])
    return create_client(url, key)


# Module-level singleton — imported by db.py as before
# Usage anywhere in the project: from src.database.config import supabase
supabase: Client = _create_supabase_client()