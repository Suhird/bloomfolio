"""CSV validator for Wealthsimple portfolio exports."""

from __future__ import annotations

import asyncio
import csv
from decimal import Decimal
from pathlib import Path

from bloomfolio.domain.validation import ValidationErrorItem, ValidationResult
from bloomfolio.observability.logging import get_logger
from bloomfolio.portfolio.normalizer import get_required_columns, normalize_columns

logger = get_logger(__name__)


async def validate_csv_file(path: str) -> ValidationResult:
    """Validate a CSV file against the Wealthsimple schema.

    Args:
        path: Path to CSV file.

    Returns:
        ValidationResult with errors and warnings.
    """
    logger.info("csv_validation_starting", path=Path(path).name)

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _validate_sync, path)


def _validate_sync(path: str) -> ValidationResult:
    """Synchronous CSV validation."""
    errors: list[ValidationErrorItem] = []
    warnings: list[ValidationErrorItem] = []
    detected_columns: list[str] = []
    unknown_columns: list[str] = []

    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                errors.append(
                    ValidationErrorItem(
                        severity="ERROR",
                        message="CSV has no header row",
                        suggested_fix="Ensure the first row contains column headers",
                    )
                )
                return ValidationResult(
                    valid=False,
                    errors=errors,
                    warnings=warnings,
                )

            detected_columns = list(reader.fieldnames)
            normalized = normalize_columns(detected_columns)

            # Check required columns
            required = get_required_columns()
            found_canonicals = set(normalized.values())
            missing_required = [r for r in required if r not in found_canonicals]

            for col in missing_required:
                errors.append(
                    ValidationErrorItem(
                        severity="ERROR",
                        field=col,
                        message=f"Required column '{col}' not found",
                        suggested_fix=f"Add a column for {col} or use an accepted alias",
                    )
                )

            # Check for unknown columns
            for raw, canonical in normalized.items():
                if canonical not in required and canonical not in [
                    "security_name",
                    "market_value",
                    "book_cost",
                    "average_cost",
                    "current_price",
                    "asset_type",
                    "exchange",
                    "sector",
                    "country",
                    "portfolio_weight",
                    "unrealized_gain_loss",
                    "unrealized_gain_loss_pct",
                ]:
                    unknown_columns.append(raw)

            # Validate rows
            row_count = 0
            for i, row in enumerate(reader, start=2):
                row_count += 1
                _validate_row(row, normalized, i, errors, warnings)

    except FileNotFoundError:
        errors.append(
            ValidationErrorItem(
                severity="ERROR",
                message=f"File not found: {path}",
                suggested_fix="Check the file path and try again",
            )
        )
        return ValidationResult(valid=False, errors=errors, warnings=warnings)
    except Exception as e:
        errors.append(
            ValidationErrorItem(
                severity="ERROR",
                message=f"Failed to read CSV: {e}",
            )
        )
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    valid = not any(e.severity == "ERROR" for e in errors)

    result = ValidationResult(
        valid=valid,
        errors=errors,
        warnings=warnings,
        row_count=row_count,
        column_count=len(detected_columns),
        detected_columns=detected_columns,
        missing_required_columns=missing_required,
        unknown_columns=unknown_columns,
    )

    logger.info(
        "csv_validation_complete",
        valid=valid,
        errors=len(errors),
        warnings=len(warnings),
        rows=row_count,
    )
    return result


def _validate_row(
    row: dict[str, str],
    normalized: dict[str, str],
    row_number: int,
    errors: list[ValidationErrorItem],
    warnings: list[ValidationErrorItem],
) -> None:
    """Validate a single row."""
    for raw, canonical in normalized.items():
        value = row.get(raw, "").strip()

        if canonical == "ticker":
            if not value:
                errors.append(
                    ValidationErrorItem(
                        severity="ERROR",
                        row_number=row_number,
                        column=raw,
                        field="ticker",
                        value=value,
                        message="Ticker is empty",
                        suggested_fix="Provide a valid ticker symbol",
                    )
                )

        elif canonical == "quantity":
            if not value:
                errors.append(
                    ValidationErrorItem(
                        severity="ERROR",
                        row_number=row_number,
                        column=raw,
                        field="quantity",
                        value=value,
                        message="Quantity is empty",
                        suggested_fix="Provide a numeric quantity",
                    )
                )
            else:
                try:
                    qty = Decimal(value)
                    if qty < 0:
                        errors.append(
                            ValidationErrorItem(
                                severity="ERROR",
                                row_number=row_number,
                                column=raw,
                                field="quantity",
                                value=value,
                                message="Quantity cannot be negative",
                                suggested_fix="Use a positive number",
                            )
                        )
                except Exception:
                    errors.append(
                        ValidationErrorItem(
                            severity="ERROR",
                            row_number=row_number,
                            column=raw,
                            field="quantity",
                            value=value,
                            message=f"Quantity '{value}' is not numeric",
                            suggested_fix="Use a decimal number like 5 or 5.25",
                        )
                    )

        elif canonical == "currency":
            if value and value.upper() not in ("CAD", "USD"):
                warnings.append(
                    ValidationErrorItem(
                        severity="WARN",
                        row_number=row_number,
                        column=raw,
                        field="currency",
                        value=value,
                        message=f"Currency '{value}' is not CAD or USD",
                        suggested_fix="Use CAD or USD",
                    )
                )

        elif canonical == "account_name":
            if not value:
                errors.append(
                    ValidationErrorItem(
                        severity="ERROR",
                        row_number=row_number,
                        column=raw,
                        field="account_name",
                        value=value,
                        message="Account name is empty",
                        suggested_fix="Provide an account name like TFSA or RRSP",
                    )
                )

        elif canonical in ("market_value", "book_cost", "average_cost", "current_price") and value:
            try:
                Decimal(value.replace("$", "").replace(",", ""))
            except Exception:
                warnings.append(
                    ValidationErrorItem(
                        severity="WARN",
                        row_number=row_number,
                        column=raw,
                        field=canonical,
                        value=value,
                        message=f"{canonical} '{value}' is not a valid decimal",
                    )
                )
