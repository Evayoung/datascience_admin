"""Configuration helpers for the portfolio admin PWA."""
from __future__ import annotations

import os
import secrets as _secrets
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).with_name(".env"))


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


PROFILE_ID = env("PORTFOLIO_PROFILE_ID", "segun-banji")
PORTFOLIO_OWNER_NAME = env("PORTFOLIO_OWNER_NAME", "Segun Banji")
ADMIN_APP_NAME = env("ADMIN_APP_NAME", f"{PORTFOLIO_OWNER_NAME} Admin")
PORTFOLIO_SITE_URL = env("PORTFOLIO_SITE_URL", "https://banjisegun.vercel.app")

# Password: only use ADMIN_PASSWORD env var; removed dangerous PORTFOLIO_SECRET_KEY fallback
ADMIN_PASSWORD = env("ADMIN_PASSWORD") or "change-me"

# Secret key: use env var if available; otherwise generate a random one per process
# WARNING: A random key means sessions are invalidated on restart. Set ADMIN_SECRET_KEY in production.
_admin_secret = env("ADMIN_SECRET_KEY") or env("FASTHTML_SECRET_KEY")
if not _admin_secret:
    _admin_secret = _secrets.token_hex(32)
ADMIN_SECRET_KEY = _admin_secret

# Session timeout in seconds (default: 24 hours)
SESSION_TIMEOUT_SECONDS = max(int(env("SESSION_TIMEOUT_SECONDS", str(24 * 3600))), 300)

SUPABASE_URL = env("SUPABASE_URL").rstrip("/")
SUPABASE_KEY = env("SUPABASE_SERVICE_ROLE_KEY") or env("SUPABASE_ANON_KEY")
SUPABASE_TIMEOUT_SECONDS = max(float(env("SUPABASE_TIMEOUT_SECONDS", "10")), 8.0)
SUPABASE_STORAGE_BUCKET = env("SUPABASE_STORAGE_BUCKET", "portfolio-images")

# Security settings
PBKDF2_ITERATIONS = max(int(env("PBKDF2_ITERATIONS", "180000")), 100_000)
ADMIN_AUTH_PORTRAIT_URL = env("ADMIN_AUTH_PORTRAIT_URL", "")
