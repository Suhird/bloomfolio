"""Portfolio aggregation utilities."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bloomfolio.domain.portfolio import Holding, Portfolio


def aggregate_by_ticker(portfolio: Portfolio) -> dict[str, list[Holding]]:
    """Aggregate holdings by ticker."""
    result: dict[str, list[Holding]] = defaultdict(list)
    for holding in portfolio.holdings:
        result[holding.ticker].append(holding)
    return dict(result)


def aggregate_by_account(portfolio: Portfolio) -> dict[str, list[Holding]]:
    """Aggregate holdings by account."""
    result: dict[str, list[Holding]] = defaultdict(list)
    for holding in portfolio.holdings:
        result[holding.account_name].append(holding)
    return dict(result)


def get_concentration_metrics(portfolio: Portfolio) -> dict[str, Decimal]:
    """Get portfolio concentration metrics."""
    totals = portfolio.get_total_value()
    metrics: dict[str, Decimal] = {}

    for ccy, money in totals.items():
        total = money.amount
        if total <= 0:
            continue

        ticker_values: dict[str, Decimal] = defaultdict(Decimal)
        for holding in portfolio.holdings:
            if holding.market_value is not None and holding.currency == ccy:
                ticker_values[holding.ticker] += holding.market_value

        sorted_values = sorted(ticker_values.values(), reverse=True)
        if sorted_values:
            metrics[f"{ccy}_top1_pct"] = (sorted_values[0] / total) * Decimal("100")
            metrics[f"{ccy}_top5_pct"] = (sum(sorted_values[:5]) / total) * Decimal("100")

    return metrics
