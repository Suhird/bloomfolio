"""Tests for CSV normalizer."""

from __future__ import annotations

from bloomfolio.portfolio.normalizer import (
    _normalize_header,
    get_required_columns,
    normalize_columns,
)


def test_normalize_columns_maps_aliases() -> None:
    headers = ["Symbol", "Qty", "CCY", "Account Type", "Market Value"]
    result = normalize_columns(headers)
    assert result["Symbol"] == "ticker"
    assert result["Qty"] == "quantity"
    assert result["CCY"] == "currency"
    assert result["Account Type"] == "account_name"
    assert result["Market Value"] == "market_value"


def test_normalize_columns_maps_wealthsimple_aliases() -> None:
    headers = [
        "Symbol",
        "Quantity",
        "Account Name",
        "Name",
        "Security Type",
        "Exchange",
        "Market Price",
        "Market Value",
        "Book Value (CAD)",
        "Book Value (Market)",
        "Market Value Currency",
        "Market Unrealized Returns",
    ]
    result = normalize_columns(headers)
    assert result["Symbol"] == "ticker"
    assert result["Quantity"] == "quantity"
    assert result["Account Name"] == "account_name"
    assert result["Name"] == "security_name"
    assert result["Security Type"] == "asset_type"
    assert result["Exchange"] == "exchange"
    assert result["Market Price"] == "current_price"
    assert result["Market Value"] == "market_value"
    assert result["Book Value (CAD)"] == "book_cost"
    # Only the first book_cost alias is mapped; the second becomes unknown
    assert result["Book Value (Market)"] == "book value market"
    assert result["Market Value Currency"] == "currency"
    assert result["Market Unrealized Returns"] == "unrealized_gain_loss"


def test_normalize_columns_ignores_unknown() -> None:
    headers = ["ticker", "quantity", "random_column"]
    result = normalize_columns(headers)
    assert result["random_column"] == "random_column"


def test_normalize_header_strips_punctuation() -> None:
    assert _normalize_header("Security Symbol!") == "security symbol"
    assert _normalize_header("  Market   Value  ") == "market value"


def test_get_required_columns() -> None:
    required = get_required_columns()
    assert "ticker" in required
    assert "quantity" in required
    assert "currency" in required
    assert "account_name" in required
