"""Portfolio overview screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import DataTable, Label, Static

from bloomfolio.tui.screens.base import BloomFolioScreen

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from bloomfolio.domain.portfolio import Portfolio
    from bloomfolio.tui.app import BloomFolioApp


class PortfolioOverviewScreen(BloomFolioScreen):
    """Portfolio overview screen."""

    BINDINGS = [
        Binding("i", "import_csv", "Import", show=True),
        Binding("r", "run_analysis", "Run", show=True),
        Binding("a", "agent_monitor", "Agents", show=True),
        Binding("x", "export", "Export", show=True),
        Binding("?", "help", "Help", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    DEFAULT_CSS = """
    PortfolioOverviewScreen {
        layout: vertical;
    }
    PortfolioOverviewScreen > Container {
        height: 1fr;
        layout: horizontal;
    }
    PortfolioOverviewScreen .panel {
        width: 1fr;
        height: 100%;
        border: solid $border;
        padding: 1;
    }
    PortfolioOverviewScreen .panel-title {
        text-style: bold;
        color: $primary;
        height: auto;
    }
    """

    def compose_content(self) -> ComposeResult:
        app: BloomFolioApp = self.app  # type: ignore[assignment]
        portfolio: Portfolio | None = app.current_portfolio

        with Container(), Horizontal():
            with Vertical(classes="panel"):
                yield Label("Holdings", classes="panel-title")
                table: DataTable[str] = DataTable(id="holdings-table")
                table.add_columns("Ticker", "Name", "Qty", "Currency", "Account", "Value", "Weight")
                if portfolio:
                    for h in portfolio.holdings:
                        table.add_row(
                            h.ticker,
                            h.security_name or "",
                            str(h.quantity),
                            h.currency,
                            h.account_name,
                            str(h.market_value or "-"),
                            f"{h.portfolio_weight:.1f}%" if h.portfolio_weight else "-",
                        )
                yield table

            with Vertical(classes="panel"):
                yield Label("Exposure", classes="panel-title")
                if portfolio:
                    totals = portfolio.get_total_value()
                    for ccy, money in totals.items():
                        yield Static(f"Total {ccy}: {money}")
                    yield Static(f"Holdings: {len(portfolio.holdings)}")
                    yield Static(f"Tickers: {len(portfolio.get_tickers())}")
                else:
                    yield Static("No portfolio imported.")

    def on_mount(self) -> None:
        """Focus the table on mount."""
        table = self.query_one("#holdings-table", DataTable)
        table.focus()
