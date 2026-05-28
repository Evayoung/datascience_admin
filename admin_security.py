"""Admin password override helpers."""
from __future__ import annotations

import hashlib
import hmac
import secrets

from config import ADMIN_PASSWORD
from supabase_admin import SupabaseAdminError, create_row, delete_row, get_row, update_row


PASSWORD_SETTING_KEY = "admin_password_hash"
PBKDF2_ITERATIONS = 180_000


def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, digest = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(candidate, digest)
    except Exception:
        return False


def _setting_value(key: str) -> str | None:
    row = get_row("admin_settings", "key", key)
    return row.get("value") if row else None


def password_override_enabled() -> bool:
    try:
        return bool(_setting_value(PASSWORD_SETTING_KEY))
    except SupabaseAdminError:
        return False


def password_matches(password: str) -> bool:
    try:
        override_hash = _setting_value(PASSWORD_SETTING_KEY)
    except SupabaseAdminError:
        override_hash = None
    if override_hash:
        return _verify_password(password, override_hash)
    return hmac.compare_digest(password, ADMIN_PASSWORD)


def change_admin_password(password: str) -> None:
    encoded = _hash_password(password)
    existing = get_row("admin_settings", "key", PASSWORD_SETTING_KEY)
    payload = {"key": PASSWORD_SETTING_KEY, "value": encoded}
    if existing:
        update_row("admin_settings", "key", PASSWORD_SETTING_KEY, payload)
    else:
        create_row("admin_settings", payload)


def reset_admin_password() -> None:
    delete_row("admin_settings", "key", PASSWORD_SETTING_KEY)
