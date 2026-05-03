"""Help modal widget."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import Grid, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult

HELP_TEXT = """
#[bold amber]BloomFolio Help[/]

#[cyan]Navigation[/]
• [b]?[/]    Show this help
• [b]q[/]    Quit current screen or app
• [b]Esc[/]  Close modal / cancel
• [b]:[/]    Open command palette
• [b]h/j/k/l[/]  Move focus left/down/up/right
• [b]g[/]    Go to top of table
• [b]G[/]    Go to bottom of table
• [b]/[/]    Search/filter table
• [b]Tab[/]  Cycle panels
• [b]Shift+Tab[/]  Reverse cycle

#[cyan]Actions[/]
• [b]i[/]    Import portfolio CSV
• [b]v[/]    Validate current CSV
• [b]r[/]    Run or rerun analysis
• [b]R[/]    Force refresh, bypass cache
• [b]p[/]    Show portfolio overview
• [b]t[/]    Show ticker detail
• [b]a[/]    Show agent run monitor
• [b]x[/]    Export current report
• [b]Ctrl+C[/]  Cancel active task
• [b]Ctrl+L[/]  Clear notifications

#[cyan]CSV Schema[/]
Required columns: ticker, quantity, currency, account_name
Optional: security_name, market_value, book_cost, average_cost, current_price, asset_type, exchange, sector, country, portfolio_weight

Press [b]q[/] or [b]Esc[/] to close this help.
"""


class HelpModal(ModalScreen[None]):
    """Help modal screen."""

    DEFAULT_CSS = """
    HelpModal {
        align: center middle;
    }
    HelpModal > Grid {
        width: 80;
        height: 40;
        border: thick $primary;
        background: $surface;
    }
    HelpModal > Grid > VerticalScroll {
        height: 1fr;
        padding: 1 2;
    }
    HelpModal > Grid > Button {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Grid():
            with VerticalScroll():
                yield Static(HELP_TEXT, markup=True)
            yield Button("Close (q)", variant="primary", id="close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.dismiss()

    def action_quit(self) -> None:
        self.dismiss()

    def action_escape(self) -> None:
        self.dismiss()
