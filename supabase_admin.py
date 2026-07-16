"""Small Supabase REST client for the admin app."""
from __future__ import annotations

import json
import base64
import mimetypes
import re
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from config import SUPABASE_KEY, SUPABASE_STORAGE_BUCKET, SUPABASE_TIMEOUT_SECONDS, SUPABASE_URL


class SupabaseAdminError(RuntimeError):
    pass


def configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def using_service_role() -> bool:
    """Best-effort local check that the configured key is a Supabase service-role JWT."""
    try:
        payload_part = SUPABASE_KEY.split(".")[1]
        payload_part += "=" * (-len(payload_part) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_part.encode("utf-8")))
        return payload.get("role") == "service_role"
    except Exception:
        return False


def _endpoint(table: str, params: dict[str, str] | None = None) -> str:
    if not configured():
        raise SupabaseAdminError("Supabase is not configured.")
    query = urlencode(params or {}, safe="(),.*")
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    return f"{url}?{query}" if query else url


def _request(method: str, table: str, params: dict[str, str] | None = None, payload: dict | None = None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(
        _endpoint(table, params),
        data=body,
        method=method,
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
    )
    try:
        with urlopen(req, timeout=SUPABASE_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else []
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise SupabaseAdminError(message or str(exc)) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise SupabaseAdminError(str(exc)) from exc


def _storage_request(method: str, path: str, data: bytes | None = None, headers: dict[str, str] | None = None):
    if not configured():
        raise SupabaseAdminError("Supabase is not configured.")
    for attempt in range(3):
        req = Request(
            f"{SUPABASE_URL}/storage/v1/{path.lstrip('/')}",
            data=data,
            method=method,
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                **(headers or {}),
            },
        )
        try:
            with urlopen(req, timeout=SUPABASE_TIMEOUT_SECONDS) as response:
                raw = response.read().decode("utf-8", errors="replace")
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            if exc.code in (400, 409) and any(word in message.lower() for word in ("already", "duplicate", "exists")):
                return {"status": "exists"}
            raise SupabaseAdminError(message or str(exc)) from exc
        except (URLError, TimeoutError, OSError) as exc:
            if attempt < 2:
                time.sleep(0.7 * (attempt + 1))
                continue
            raise SupabaseAdminError(str(exc)) from exc
    return {}


def list_rows(table: str, order: str = "sort_order.asc", limit: int = 250) -> list[dict]:
    return _request("GET", table, {"select": "*", "order": order, "limit": str(limit)})


def list_rows_page(table: str, page: int = 1, per_page: int = 25, order: str = "sort_order.asc") -> tuple[list[dict], int]:
    """Fetch a page of rows and return (rows, total_count)."""
    total = count_rows(table)
    offset = (max(page, 1) - 1) * per_page
    rows = _request("GET", table, {"select": "*", "order": order, "limit": str(per_page), "offset": str(offset)})
    return rows, total


def count_rows(table: str) -> int:
    """Return the total row count for a table using Supabase's count header."""
    if not configured():
        return 0
    url = _endpoint(table, {"select": "id"})
    req = Request(
        url,
        method="GET",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Accept": "application/json",
            "Prefer": "count=exact",
            "Range-Unit": "items",
            "Range": "0-0",
        },
    )
    try:
        with urlopen(req, timeout=SUPABASE_TIMEOUT_SECONDS) as response:
            content_range = response.headers.get("Content-Range", "")
            if "/" in content_range:
                total = content_range.split("/")[-1]
                return int(total) if total != "*" else 0
            return 0
    except Exception:
        return 0


def get_row(table: str, pk: str, value: str) -> dict | None:
    rows = _request("GET", table, {"select": "*", pk: f"eq.{value}", "limit": "1"})
    return rows[0] if rows else None


def create_row(table: str, payload: dict) -> dict | None:
    rows = _request("POST", table, payload=payload)
    return rows[0] if rows else None


def update_row(table: str, pk: str, value: str, payload: dict) -> dict | None:
    rows = _request("PATCH", table, {pk: f"eq.{value}"}, payload)
    return rows[0] if rows else None


def delete_row(table: str, pk: str, value: str) -> None:
    _request("DELETE", table, {pk: f"eq.{value}"})


def option_rows(table: str, label_fields: tuple[str, ...], value_field: str, order: str = "sort_order.asc") -> list[tuple[str, str]]:
    rows = list_rows(table, order=order)
    options = []
    for row in rows:
        raw_value = row.get(value_field)
        if raw_value is None:
            continue  # Skip rows missing the value field
        label = " - ".join(str(row.get(field) or "") for field in label_fields).strip(" -")
        options.append((str(raw_value), label or str(raw_value)))
    return options


def encoded_pk(value: object) -> str:
    return quote(str(value), safe="")


_storage_bucket_ensured: set[str] = set()


def ensure_storage_bucket(bucket: str = SUPABASE_STORAGE_BUCKET) -> None:
    """Ensure the storage bucket exists. Caches the result to avoid repeated API calls."""
    if bucket in _storage_bucket_ensured:
        return
    payload = {
        "id": bucket,
        "name": bucket,
        "public": True,
        "file_size_limit": 5242880,
        "allowed_mime_types": ["image/png", "image/jpeg", "image/webp", "image/gif", "image/svg+xml"],
    }
    result = _storage_request(
        "POST",
        "bucket",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    _storage_bucket_ensured.add(bucket)


def public_storage_url(path: str, bucket: str = SUPABASE_STORAGE_BUCKET) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{quote(path, safe='/')}"


def delete_storage_file(public_url: str) -> bool:
    """Delete a file from Supabase Storage given its public URL. Returns True if deleted."""
    if not configured() or not public_url:
        return False
    try:
        # Extract the object path from the public URL
        # Format: {SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}
        prefix = f"{SUPABASE_URL}/storage/v1/object/public/"
        if not public_url.startswith(prefix):
            return False
        relative = public_url[len(prefix):]
        # Split into bucket and path
        parts = relative.split("/", 1)
        if len(parts) != 2:
            return False
        bucket, object_path = parts
        _storage_request(
            "DELETE",
            f"object/{bucket}/{quote(object_path, safe='/')}",
        )
        return True
    except Exception:
        return False


def upload_image(filename: str, content: bytes, content_type: str | None = None, folder: str = "uploads") -> str:
    if not content:
        raise SupabaseAdminError("No image file was uploaded.")
    guessed_type = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    if not guessed_type.startswith("image/"):
        raise SupabaseAdminError("Only image files can be uploaded.")

    ensure_storage_bucket()
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", filename.strip()).strip(".-") or "image"
    safe_folder = re.sub(r"[^A-Za-z0-9/_-]+", "-", folder.strip("/")) or "uploads"
    object_path = f"{safe_folder}/{int(time.time())}-{uuid.uuid4().hex[:8]}-{safe_name}"
    _storage_request(
        "POST",
        f"object/{SUPABASE_STORAGE_BUCKET}/{quote(object_path, safe='/')}",
        data=content,
        headers={
            "Content-Type": guessed_type,
            "x-upsert": "true",
        },
    )
    return public_storage_url(object_path)
