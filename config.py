"""Configuration helpers for the portfolio admin PWA."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).with_name(".env"))


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


PROFILE_ID = env("PORTFOLIO_PROFILE_ID", "segun-banji")
PORTFOLIO_OWNER_NAME = env("PORTFOLIO_OWNER_NAME", "Segun Banji")
ADMIN_APP_NAME = env("ADMIN_APP_NAME", f"{PORTFOLIO_OWNER_NAME} Admin")
PORTFOLIO_SITE_URL = env("PORTFOLIO_SITE_URL", "https://banjisegun.vercel.app")
ADMIN_PASSWORD = env("ADMIN_PASSWORD") or env("PORTFOLIO_SECRET_KEY") or "change-me"
ADMIN_SECRET_KEY = (
    env("ADMIN_SECRET_KEY")
    or env("FASTHTML_SECRET_KEY")
    or env("PORTFOLIO_SECRET_KEY")
    or "datascience-admin-local-secret"
)
SUPABASE_URL = env("SUPABASE_URL").rstrip("/")
SUPABASE_KEY = env("SUPABASE_SERVICE_ROLE_KEY") or env("SUPABASE_ANON_KEY")
SUPABASE_TIMEOUT_SECONDS = max(float(env("SUPABASE_TIMEOUT_SECONDS", "10")), 8.0)
SUPABASE_STORAGE_BUCKET = env("SUPABASE_STORAGE_BUCKET", "portfolio-images")
