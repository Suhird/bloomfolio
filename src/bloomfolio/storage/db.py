"""SQLite database management."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import aiosqlite

from bloomfolio.config.settings import get_settings
from bloomfolio.observability.logging import get_logger

logger = get_logger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS portfolios (
    id TEXT PRIMARY KEY,
    imported_at TEXT NOT NULL,
    source_file_name TEXT NOT NULL,
    base_currency TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    security_name TEXT,
    quantity TEXT NOT NULL,
    currency TEXT NOT NULL,
    account_name TEXT NOT NULL,
    market_value TEXT,
    book_cost TEXT,
    average_cost TEXT,
    current_price TEXT,
    asset_type TEXT,
    exchange TEXT,
    sector TEXT,
    country TEXT,
    portfolio_weight TEXT,
    unrealized_gain_loss TEXT,
    unrealized_gain_loss_pct TEXT,
    source_row_number INTEGER,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
);

CREATE TABLE IF NOT EXISTS analysis_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL,
    tickers TEXT NOT NULL,
    model_provider TEXT,
    model_name TEXT,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS agent_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    stage TEXT NOT NULL,
    summary TEXT,
    key_points TEXT,
    risks TEXT,
    confidence REAL,
    raw_output TEXT,
    parsed_output TEXT,
    validation_status TEXT,
    model_name TEXT,
    prompt_hash TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    rating TEXT,
    action_label TEXT,
    time_horizon TEXT,
    thesis TEXT,
    bull_case TEXT,
    bear_case TEXT,
    risk_notes TEXT,
    portfolio_context_notes TEXT,
    confidence REAL,
    key_uncertainties TEXT,
    disclaimer TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    actor TEXT,
    entity_type TEXT,
    entity_id TEXT,
    before_json TEXT,
    after_json TEXT,
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS cache_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT NOT NULL UNIQUE,
    value_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
"""


class Database:
    """Async SQLite database manager."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.settings = get_settings()
        self.db_path = db_path or self.settings.db_path
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> aiosqlite.Connection:
        """Get or create database connection."""
        if self._connection is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
            logger.info("database_connected", path=str(self.db_path))
        return self._connection

    async def initialize(self) -> None:
        """Create tables if they don't exist."""
        conn = await self.connect()
        await conn.executescript(SCHEMA)
        await conn.commit()
        logger.info("database_initialized")

    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("database_closed")

    async def execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> aiosqlite.Cursor:
        """Execute SQL."""
        conn = await self.connect()
        return await conn.execute(sql, parameters)

    async def executemany(self, sql: str, parameters: list[tuple[Any, ...]]) -> aiosqlite.Cursor:
        """Execute many."""
        conn = await self.connect()
        return await conn.executemany(sql, parameters)

    async def fetchone(self, sql: str, parameters: tuple[Any, ...] = ()) -> aiosqlite.Row | None:
        """Fetch one row."""
        conn = await self.connect()
        async with conn.execute(sql, parameters) as cursor:
            return await cursor.fetchone()

    async def fetchall(self, sql: str, parameters: tuple[Any, ...] = ()) -> list[aiosqlite.Row]:
        """Fetch all rows."""
        conn = await self.connect()
        cursor = await conn.execute(sql, parameters)
        rows = await cursor.fetchall()
        return list(rows)

    async def commit(self) -> None:
        """Commit transaction."""
        conn = await self.connect()
        await conn.commit()


_db: Database | None = None


async def get_db() -> Database:
    """Get or create singleton database instance."""
    global _db
    if _db is None:
        _db = Database()
        await _db.initialize()
    return _db
