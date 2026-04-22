"""Shared helpers for marketing automation services."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def utcnow() -> datetime:
    """Return a timezone-aware current UTC timestamp."""
    return datetime.now(timezone.utc)


def ensure_datetime(value: Any) -> datetime | None:
    """Convert webhook or Firestore values into timezone-aware datetimes."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 10_000_000_000:
            timestamp /= 1000.0
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    raise TypeError(f"Unsupported datetime value: {value!r}")


def stable_id(prefix: str, *parts: Any) -> str:
    """Generate deterministic IDs for idempotent documents."""
    raw = "::".join(str(part) for part in parts if part is not None)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}_{digest}"


def payload_hash(payload: dict[str, Any]) -> str:
    """Generate a stable hash for event payload storage."""
    serialized = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def excerpt(payload: dict[str, Any], max_length: int = 500) -> str:
    """Create a compact JSON excerpt safe for event logs."""
    serialized = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
    return serialized[:max_length]
