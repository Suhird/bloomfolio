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
