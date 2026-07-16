"""Admin password override helpers and security utilities."""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from collections import defaultdict
from datetime import datetime, timezone

from config import ADMIN_PASSWORD, PBKDF2_ITERATIONS
from supabase_admin import SupabaseAdminError, create_row, delete_row, get_row, list_rows, update_row


PASSWORD_SETTING_KEY = "admin_password_hash"

# --- CSRF Protection ---

CSRF_TOKEN_LENGTH = 32
CSRF_SECRET_SEPARATOR = "|"


def generate_csrf_token(session_secret: str, session_id: str) -> str:
    """Generate a CSRF token tied to the session."""
    token = secrets.token_hex(CSRF_TOKEN_LENGTH)
    payload = f"{session_id}{CSRF_SECRET_SEPARATOR}{token}"
    signature = hmac.new(
        session_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{token}{CSRF_SECRET_SEPARATOR}{signature}"


def verify_csrf_token(session_secret: str, session_id: str, token: str) -> bool:
    """Verify a CSRF token matches the session."""
    if not token:
        return False
    parts = token.split(CSRF_SECRET_SEPARATOR)
    if len(parts) != 2:
        return False
    raw_token, provided_signature = parts
    payload = f"{session_id}{CSRF_SECRET_SEPARATOR}{raw_token}"
    expected_signature = hmac.new(
        session_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(provided_signature, expected_signature)


# --- Brute-force Protection ---

_LOGIN_ATTEMPTS: dict[str, list[float]] = defaultdict(list)
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 300  # 5 minutes


def _is_locked_out(identifier: str) -> bool:
    """Check if an identifier (IP or username) is locked out due to too many failed attempts."""
    now = time.time()
    cutoff = now - _LOCKOUT_SECONDS
    # Clean old attempts
    _LOGIN_ATTEMPTS[identifier] = [t for t in _LOGIN_ATTEMPTS[identifier] if t > cutoff]
    return len(_LOGIN_ATTEMPTS[identifier]) >= _MAX_ATTEMPTS


def record_failed_attempt(identifier: str) -> None:
    """Record a failed login attempt."""
    _LOGIN_ATTEMPTS[identifier].append(time.time())


def clear_attempts(identifier: str) -> None:
    """Clear login attempts after successful authentication."""
    _LOGIN_ATTEMPTS.pop(identifier, None)


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
    """Change the admin password, handling race conditions gracefully."""
    encoded = _hash_password(password)
    payload = {"key": PASSWORD_SETTING_KEY, "value": encoded}
    existing = get_row("admin_settings", "key", PASSWORD_SETTING_KEY)
    if existing:
        try:
            update_row("admin_settings", "key", PASSWORD_SETTING_KEY, payload)
        except SupabaseAdminError:
            # Race condition: row may have been deleted between get_row and update_row
            # Try creating instead
            create_row("admin_settings", payload)
    else:
        try:
            create_row("admin_settings", payload)
        except SupabaseAdminError:
            # Race condition: row may have been created between get_row and create_row
            # Try updating instead
            update_row("admin_settings", "key", PASSWORD_SETTING_KEY, payload)


def reset_admin_password() -> None:
    delete_row("admin_settings", "key", PASSWORD_SETTING_KEY)


# --- Audit Logging ---

AUDIT_LOG_KEY = "admin_audit_log"


def log_admin_action(action: str, details: str = "", ip_address: str = "") -> None:
    """Log an admin action to the audit log stored in Supabase admin_settings."""
    entry = {
        "action": action,
        "details": details,
        "ip": ip_address,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        existing = get_row("admin_settings", "key", AUDIT_LOG_KEY)
        if existing:
            logs = json.loads(existing.get("value", "[]"))
        else:
            logs = []
        # Keep last 100 entries
        logs.append(entry)
        logs = logs[-100:]
        payload = {"key": AUDIT_LOG_KEY, "value": json.dumps(logs)}
        if existing:
            update_row("admin_settings", "key", AUDIT_LOG_KEY, payload)
        else:
            create_row("admin_settings", payload)
    except SupabaseAdminError:
        pass  # Best-effort logging; don't break the app if logging fails


def get_audit_logs(limit: int = 20) -> list[dict]:
    """Retrieve recent audit log entries."""
    try:
        existing = get_row("admin_settings", "key", AUDIT_LOG_KEY)
        if existing:
            logs = json.loads(existing.get("value", "[]"))
            return list(reversed(logs[-limit:]))
    except (SupabaseAdminError, json.JSONDecodeError):
        pass
    return []
