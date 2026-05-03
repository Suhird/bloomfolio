"""Cache management."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from bloomfolio.observability.logging import get_logger
from bloomfolio.storage.db import get_db

logger = get_logger(__name__)

DEFAULT_TTLS = {
    "quotes": timedelta(minutes=15),
    "historical_prices": timedelta(hours=24),
    "fundamentals": timedelta(days=7),
    "news": timedelta(hours=6),
    "sentiment": timedelta(hours=6),
    "llm_outputs": timedelta(hours=24),
}


def _make_key(prefix: str, *parts: str) -> str:
    """Create cache key from parts."""
    key = "|".join([prefix, *parts])
    return hashlib.sha256(key.encode()).hexdigest()


async def get_cached(key: str) -> Any | None:
    """Get value from cache if not expired."""
    db = await get_db()
    row = await db.fetchone(
        "SELECT value_json, expires_at FROM cache_entries WHERE cache_key = ?",
        (key,),
    )
    if row is None:
        return None

    expires = datetime.fromisoformat(row["expires_at"])
    if datetime.now(UTC) > expires:
        await db.execute("DELETE FROM cache_entries WHERE cache_key = ?", (key,))
        await db.commit()
        return None

    return json.loads(row["value_json"])


async def set_cached(key: str, value: Any, ttl: timedelta | None = None) -> None:
    """Set value in cache with TTL."""
    if ttl is None:
        ttl = DEFAULT_TTLS["llm_outputs"]

    expires = datetime.now(UTC) + ttl
    db = await get_db()
    await db.execute(
        """
        INSERT OR REPLACE INTO cache_entries (cache_key, value_json, created_at, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            key,
            json.dumps(value, default=str),
            datetime.now(UTC).isoformat(),
            expires.isoformat(),
        ),
    )
    await db.commit()


async def clear_cache(prefix: str | None = None) -> int:
    """Clear cache entries. Returns count deleted."""
    db = await get_db()
    if prefix:
        cursor = await db.execute("DELETE FROM cache_entries WHERE cache_key LIKE ?", (f"{prefix}%",))
    else:
        cursor = await db.execute("DELETE FROM cache_entries")
    await db.commit()
    return cursor.rowcount
