"""Schema help modal."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.binding import Binding
from textual.containers import Grid, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult

SCHEMA_HELP_TEXT = """
#[bold amber]Wealthsimple CSV Schema Help[/]

#[cyan]Required Columns[/]
• [b]ticker[/]         Security symbol (e.g., VFV, XEQT, AAPL, SHOP.TO)
• [b]quantity[/]       Units/shares held (decimal, >= 0)
• [b]currency[/]       CAD or USD
• [b]account_name[/]   Account label (e.g., TFSA, RRSP, Personal)

#[cyan]Strongly Recommended Columns[/]
• [b]security_name[/]     Human-readable name
• [b]market_value[/]      Current total market value
• [b]book_cost[/]         Total cost basis
• [b]average_cost[/]      Average cost per share
• [b]current_price[/]     Current price per share
• [b]asset_type[/]        stock, etf, cash, crypto, bond, other
• [b]exchange[/]          TSX, NYSE, NASDAQ, NEO, etc.
• [b]sector[/]            Sector when known
• [b]country[/]           Issuer/holding country
• [b]portfolio_weight[/]  Percentage weight
• [b]unrealized_gain_loss[/]     Absolute gain/loss
• [b]unrealized_gain_loss_pct[/]  Percentage gain/loss

#[cyan]Accepted Aliases[/]
ticker: symbol, security symbol, instrument symbol, stock symbol
quantity: qty, shares, units, number of shares
market_value: market value, current value, value, total value
book_cost: book cost, cost basis, adjusted cost base, acb
account_name: account, account name, account type, portfolio

#[cyan]Example Header[/]
ticker,security_name,quantity,currency,account_name,market_value,book_cost,average_cost,current_price,asset_type,exchange

#[cyan]Example Row[/]
VFV,Vanguard S&P 500 Index ETF,25.5,CAD,TFSA,3450.25,3100.00,121.57,135.30,ETF,TSX

#[cyan]Notes[/]
• Cash rows (asset_type=cash) are accepted but not analyzed
• Duplicate ticker+account rows are allowed and aggregated
• Empty tickers or quantities are invalid
• Percentage columns may be 12.3, 12.3%, or 0.123
"""


class SchemaHelpModal(ModalScreen[None]):
    """Schema help modal screen."""

    BINDINGS = [
        Binding("q", "quit", "Close", show=False),
        Binding("escape", "escape", "Close", show=False),
    ]

    DEFAULT_CSS = """
    SchemaHelpModal {
        align: center middle;
    }
    SchemaHelpModal > Grid {
        width: 90;
        height: 45;
        border: thick $primary;
        background: $surface;
    }
    SchemaHelpModal > Grid > VerticalScroll {
        height: 1fr;
        padding: 1 2;
    }
    SchemaHelpModal > Grid > Button {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Grid():
            with VerticalScroll():
                yield Static(SCHEMA_HELP_TEXT, markup=True)
            yield Button("Close (q)", variant="primary", id="close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.dismiss()

    def action_quit(self) -> None:
        self.dismiss()

    def action_escape(self) -> None:
        self.dismiss()
