"""Column alias normalizer."""

from __future__ import annotations

import re

# Mapping from canonical name to list of accepted aliases
COLUMN_ALIASES: dict[str, list[str]] = {
    "ticker": [
        "ticker",
        "symbol",
        "security symbol",
        "instrument symbol",
        "stock symbol",
        "holdings symbol",
    ],
    "security_name": [
        "name",
        "security name",
        "instrument name",
        "asset name",
        "holding name",
        "description",
    ],
    "quantity": [
        "quantity",
        "qty",
        "shares",
        "units",
        "number of shares",
        "quantity held",
    ],
    "currency": [
        "currency",
        "ccy",
        "currency code",
        "market value currency",
        "market price currency",
        "book value currency cad",
        "book value currency market",
    ],
    "account_name": [
        "account",
        "account name",
        "account type",
        "account label",
        "portfolio",
        "wealthsimple account",
    ],
    "market_value": [
        "market value",
        "current value",
        "value",
        "total value",
        "position value",
    ],
    "book_cost": [
        "book cost",
        "cost basis",
        "adjusted cost base",
        "acb",
        "total cost",
        "book value cad",
        "book value market",
    ],
    "average_cost": [
        "average cost",
        "avg cost",
        "average price",
        "avg price",
        "average purchase price",
    ],
    "current_price": [
        "current price",
        "market price",
        "last price",
        "price",
        "quote price",
    ],
    "asset_type": [
        "asset type",
        "type",
        "security type",
        "instrument type",
    ],
    "exchange": [
        "exchange",
        "market",
        "listing exchange",
    ],
    "sector": [
        "sector",
    ],
    "country": [
        "country",
    ],
    "portfolio_weight": [
        "weight",
        "allocation",
        "portfolio weight",
        "percentage of portfolio",
    ],
    "unrealized_gain_loss": [
        "unrealized gain loss",
        "unrealized gain/loss",
        "gain loss",
        "gain/loss",
        "market unrealized returns",
    ],
    "unrealized_gain_loss_pct": [
        "unrealized gain loss pct",
        "unrealized gain/loss %",
        "gain loss %",
        "gain/loss %",
    ],
}


def _normalize_header(header: str) -> str:
    """Normalize a header string for comparison."""
    # Lowercase, remove extra whitespace, remove punctuation
    cleaned = header.lower().strip()
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def normalize_columns(headers: list[str]) -> dict[str, str]:
    """Map raw CSV headers to canonical field names.

    Returns:
        Dict mapping raw header to canonical field name.
    """
    result: dict[str, str] = {}
    used_canonicals: set[str] = set()

    for raw in headers:
        normalized = _normalize_header(raw)
        matched = False

        for canonical, aliases in COLUMN_ALIASES.items():
            if canonical in used_canonicals:
                continue
            if normalized in aliases or normalized == canonical:
                result[raw] = canonical
                used_canonicals.add(canonical)
                matched = True
                break

        if not matched:
            result[raw] = normalized

    return result


def get_required_columns() -> list[str]:
    """Get list of required canonical columns."""
    return ["ticker", "quantity", "currency", "account_name"]
