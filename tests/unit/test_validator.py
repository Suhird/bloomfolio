"""Tests for CSV validator."""

from __future__ import annotations

from pathlib import Path

import pytest

from bloomfolio.portfolio.validator import validate_csv_file

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.mark.asyncio
async def test_valid_csv_passes() -> None:
    path = FIXTURES_DIR / "wealthsimple_valid.csv"
    result = await validate_csv_file(str(path))
    assert result.valid is True
    assert result.row_count == 5


@pytest.mark.asyncio
async def test_missing_required_columns_fails() -> None:
    path = FIXTURES_DIR / "wealthsimple_missing_columns.csv"
    result = await validate_csv_file(str(path))
    assert result.valid is False
    assert any("ticker" in (e.field or "") for e in result.errors)


@pytest.mark.asyncio
async def test_bad_values_reports_errors() -> None:
    path = FIXTURES_DIR / "wealthsimple_bad_values.csv"
    result = await validate_csv_file(str(path))
    assert result.valid is False
    assert any("quantity" in (e.field or "") for e in result.errors)
