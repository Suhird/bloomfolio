"""Audit logging."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from bloomfolio.domain.enums import AuditEventType
from bloomfolio.observability.logging import get_logger
from bloomfolio.storage.db import get_db

logger = get_logger(__name__)


async def log_audit_event(
    event_type: AuditEventType,
    actor: str = "system",
    entity_type: str | None = None,
    entity_id: str | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Log an audit event.

    Args:
        event_type: Type of event.
        actor: Who/what triggered the event.
        entity_type: Type of entity affected.
        entity_id: ID of entity affected.
        before: State before the event.
        after: State after the event.
        metadata: Additional metadata.
    """
    db = await get_db()
    await db.execute(
        """
        INSERT INTO audit_events (timestamp, event_type, actor, entity_type, entity_id, before_json, after_json, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(UTC).isoformat(),
            event_type.value,
            actor,
            entity_type,
            entity_id,
            json.dumps(before) if before else None,
            json.dumps(after) if after else None,
            json.dumps(metadata) if metadata else None,
        ),
    )
    await db.commit()
    logger.info(
        "audit_event_logged",
        event_type=event_type.value,
        entity_type=entity_type,
        entity_id=entity_id,
    )
