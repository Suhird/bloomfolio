"""Structured output utilities."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ValidationError

from bloomfolio.domain.reports import TaskResult


def extract_json_from_markdown(text: str) -> str:
    """Extract JSON from markdown code blocks."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def safe_json_parse(text: str) -> dict[str, Any] | None:
    """Safely parse JSON, returning None on failure."""
    try:
        result: dict[str, Any] = json.loads(text)
        return result
    except json.JSONDecodeError:
        return None


def validate_schema[T: BaseModel](data: dict[str, Any], schema: type[T]) -> TaskResult[T]:
    """Validate dict against Pydantic schema.

    Args:
        data: Dictionary to validate.
        schema: Pydantic model class.

    Returns:
        TaskResult with validated instance or error.
    """
    try:
        instance = schema.model_validate(data)
        return TaskResult.success(instance)
    except ValidationError as e:
        return TaskResult.failure(str(e))
