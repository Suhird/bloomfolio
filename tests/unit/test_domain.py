"""Tests for domain models."""

from __future__ import annotations

from decimal import Decimal

import pytest

from bloomfolio.domain.enums import AssetType
from bloomfolio.domain.money import Money
from bloomfolio.domain.portfolio import Holding, Portfolio


def test_money_addition() -> None:
    a = Money(amount=Decimal("100.50"), currency="CAD")
    b = Money(amount=Decimal("50.25"), currency="CAD")
    result = a.add(b)
    assert result.amount == Decimal("150.75")
    assert result.currency == "CAD"


def test_money_addition_different_currency_fails() -> None:
    a = Money(amount=Decimal("100"), currency="CAD")
    b = Money(amount=Decimal("50"), currency="USD")
    with pytest.raises(ValueError):
        a.add(b)


def test_holding_is_cash() -> None:
    cash = Holding(
        ticker="CASH",
        quantity=Decimal("1000"),
        currency="CAD",
        account_name="TFSA",
        asset_type=AssetType.CASH,
    )
    assert cash.is_cash() is True

    stock = Holding(
        ticker="AAPL",
        quantity=Decimal("10"),
        currency="USD",
        account_name="Personal",
    )
    assert stock.is_cash() is False


def test_portfolio_get_tickers() -> None:
    portfolio = Portfolio(
        source_file_name="test.csv",
        holdings=[
            Holding(ticker="AAPL", quantity=Decimal("10"), currency="USD", account_name="Personal"),
            Holding(ticker="CASH", quantity=Decimal("100"), currency="CAD", account_name="TFSA", asset_type=AssetType.CASH),
        ],
    )
    tickers = portfolio.get_tickers()
    assert tickers == ["AAPL"]
