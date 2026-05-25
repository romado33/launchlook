"""
env.py - small helpers for loading env vars in serverless handlers.

Vercel injects env vars via process.env (which Python sees as os.environ).
Locally, scripts/.env is loaded via python-dotenv when available.

Use require_env() at the top of a handler to fail fast with a clear message.
Use optional_env() for things that have safe defaults.
"""

from __future__ import annotations

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class MissingEnvError(RuntimeError):
    """Raised when a required env var is unset."""


def require_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise MissingEnvError(
            f"Required env var {key} is not set. "
            "Set it in Vercel (Project -> Settings -> Environment Variables) "
            "or in your local .env file."
        )
    return val


def optional_env(key: str, default: str = "") -> str:
    return os.getenv(key) or default
