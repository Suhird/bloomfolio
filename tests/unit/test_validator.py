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


@pytest.mark.asyncio
async def test_real_wealthsimple_export_passes() -> None:
    path = FIXTURES_DIR / "wealthsimple_real_export.csv"
    result = await validate_csv_file(str(path))
    assert result.valid is True
    assert result.row_count == 8
    assert "Symbol" not in result.unknown_columns


@pytest.mark.asyncio
async def test_real_wealthsimple_export_skips_footer_row() -> None:
    path = FIXTURES_DIR / "wealthsimple_real_export.csv"
    result = await validate_csv_file(str(path))
    # Footer row should not trigger an empty-ticker error
    assert not any(
        "empty" in e.message.lower() and e.field == "ticker" for e in result.errors
    )
