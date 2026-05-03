"""Export modal."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, RadioButton, RadioSet, Static

from bloomfolio.storage.export import export_portfolio_json, export_portfolio_markdown

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from bloomfolio.domain.portfolio import Portfolio


class ExportScreen(ModalScreen[None]):
    """Export report modal overlay."""

    BINDINGS = [
        Binding("q", "quit", "Back", show=True),
        Binding("escape", "escape", "Back", show=True),
    ]

    DEFAULT_CSS = """
    ExportScreen {
        align: center middle;
    }
    ExportScreen > Container {
        width: 80;
        height: auto;
        padding: 2 4;
        border: thick $primary;
        background: $surface;
    }
    """

    def __init__(self, portfolio: Portfolio) -> None:
        super().__init__()
        self.portfolio = portfolio

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Export Report", classes="title")
            yield Static(f"Portfolio: {self.portfolio.source_file_name}")
            yield Static(f"Holdings: {len(self.portfolio.holdings)}")

            yield Label("Format:")
            yield RadioSet(
                RadioButton("Markdown", value=True),
                RadioButton("JSON"),
                id="format-radio",
            )

            yield Input(
                placeholder="Export path (optional)",
                id="path-input",
            )

            with Horizontal():
                yield Button("Export", variant="primary", id="export-btn")
                yield Button("Back (q)", variant="error", id="back-btn")

            yield Static("", id="status")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "export-btn":
            self._do_export()
        elif event.button.id == "back-btn":
            self.dismiss()

    def action_quit(self) -> None:
        """Close modal."""
        self.dismiss()

    def action_escape(self) -> None:
        """Close modal."""
        self.dismiss()

    def _do_export(self) -> None:
        """Export report."""
        status = self.query_one("#status", Static)
        path_input = self.query_one("#path-input", Input)
        path_str = path_input.value.strip()

        # Determine format
        radio_set = self.query_one("#format-radio", RadioSet)
        selected = radio_set.pressed_button
        fmt = "markdown" if selected and "Markdown" in str(selected.label) else "json"

        if not path_str:
            default_name = f"bloomfolio_report.{fmt}"
            path = Path.home() / default_name
        else:
            path = Path(path_str)

        try:
            # Get results from app state if available
            results = getattr(self.app, "analysis_results", {})

            if fmt == "markdown":
                export_portfolio_markdown(self.portfolio, results, path)
            else:
                export_portfolio_json(self.portfolio, results, path)

            status.update(f"Exported to {path}")
            status.styles.color = "green"
        except Exception as e:
            status.update(f"Export failed: {e}")
            status.styles.color = "red"
