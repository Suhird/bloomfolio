"""Validation models for CSV and other inputs."""

from __future__ import annotations

from pydantic import BaseModel


class ValidationErrorItem(BaseModel):
    """Single validation error."""

    severity: str  # ERROR, WARN
    row_number: int | None = None
    column: str | None = None
    field: str | None = None
    value: str | None = None
    message: str = ""
    suggested_fix: str = ""


class ValidationResult(BaseModel):
    """CSV validation result."""

    valid: bool
    errors: list[ValidationErrorItem] = []
    warnings: list[ValidationErrorItem] = []
    row_count: int = 0
    column_count: int = 0
    detected_columns: list[str] = []
    missing_required_columns: list[str] = []
    unknown_columns: list[str] = []

    def has_errors(self) -> bool:
        return any(e.severity == "ERROR" for e in self.errors)

    def get_diagnostics(self) -> list[ValidationErrorItem]:
        return self.errors + self.warnings
