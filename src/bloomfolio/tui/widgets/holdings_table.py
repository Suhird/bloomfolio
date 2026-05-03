"""Enhanced holdings table with selection and rating columns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.widgets import DataTable

if TYPE_CHECKING:
    from bloomfolio.domain.portfolio import Portfolio
    from bloomfolio.domain.reports import TickerAnalysisResult


class HoldingsTable(DataTable[str]):
    """Holdings table with selection cursor and analysis rating column."""

    DEFAULT_CSS = """
    HoldingsTable {
        height: 100%;
        border: solid $border;
    }
    HoldingsTable .datatable--cursor {
        background: $primary-darken-2;
    }
    """

    def __init__(self) -> None:
        super().__init__(id="holdings-table")
        self.cursor_type = "row"
        self.zebra_stripes = True

    def load_portfolio(
        self,
        portfolio: Portfolio | None,
        analysis_results: dict[str, TickerAnalysisResult],
    ) -> None:
        """Populate table from portfolio and optional analysis results."""
        self.clear(columns=True)
        self.add_columns("Ticker", "Name", "Qty", "Currency", "Account", "Value", "Rating")

        if not portfolio:
            return

        for h in portfolio.holdings:
            result = analysis_results.get(h.ticker)
            rating = "-"
            if result and result.decision:
                rating = str(result.decision.rating)
            self.add_row(
                h.ticker,
                h.security_name or "",
                str(h.quantity),
                h.currency,
                h.account_name,
                str(h.market_value or "-"),
                rating,
            )

    def get_selected_ticker(self) -> str | None:
        """Return the ticker at the current cursor row."""
        cursor = self.cursor_row
        if cursor is None or cursor < 0:
            return None
        row = self.get_row_at(cursor)
        return row[0] if row else None
