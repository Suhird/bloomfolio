"""Tests for CSV importer."""

from __future__ import annotations

from pathlib import Path

import pytest

from bloomfolio.domain.enums import AssetType
from bloomfolio.domain.exceptions import PortfolioValidationError
from bloomfolio.portfolio.csv_importer import import_csv

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.mark.asyncio
async def test_import_valid_csv() -> None:
    path = FIXTURES_DIR / "wealthsimple_valid.csv"
    portfolio = await import_csv(str(path))
    assert len(portfolio.holdings) == 5
    assert portfolio.source_file_name == "wealthsimple_valid.csv"

    # Check first holding
    vfv = next(h for h in portfolio.holdings if h.ticker == "VFV")
    assert vfv.quantity == 25.5
    assert vfv.currency == "CAD"

    # Check cash handling
    cash = next(h for h in portfolio.holdings if h.ticker == "CASH")
    assert cash.is_cash() is True


@pytest.mark.asyncio
async def test_import_invalid_csv_raises() -> None:
    path = FIXTURES_DIR / "wealthsimple_missing_columns.csv"
    with pytest.raises(PortfolioValidationError):
        await import_csv(str(path))


@pytest.mark.asyncio
async def test_import_real_wealthsimple_export() -> None:
    path = FIXTURES_DIR / "wealthsimple_real_export.csv"
    portfolio = await import_csv(str(path))
    assert len(portfolio.holdings) == 8
    assert portfolio.source_file_name == "wealthsimple_real_export.csv"

    # Check mapped fields
    from decimal import Decimal

    xeqt = next(h for h in portfolio.holdings if h.ticker == "XEQT")
    assert xeqt.quantity == Decimal("336.5014")
    assert xeqt.currency == "CAD"
    assert xeqt.asset_type == AssetType.ETF
    assert xeqt.market_value is not None
    assert xeqt.book_cost is not None

    # Check equity mapping
    rei = next(h for h in portfolio.holdings if h.ticker == "REI.UN")
    assert rei.asset_type == AssetType.STOCK

    # Check precious metal mapping
    gold = next(h for h in portfolio.holdings if h.ticker == "GOLD")
    assert gold.asset_type == AssetType.OTHER
