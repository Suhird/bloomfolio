"""Startup screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from bloomfolio.tui.widgets.footer import BloomFolioFooter

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from bloomfolio.tui.app import BloomFolioApp


class StartupScreen(Screen[None]):
    """Application startup screen."""

    DEFAULT_CSS = """
    StartupScreen {
        align: center middle;
    }
    StartupScreen > Container {
        width: 80;
        height: auto;
        padding: 2 4;
        border: thick $primary;
        background: $surface;
    }
    StartupScreen .title {
        text-align: center;
        color: $primary;
        text-style: bold;
        height: auto;
    }
    StartupScreen .subtitle {
        text-align: center;
        color: $text-muted;
        height: auto;
    }
    StartupScreen .status {
        margin: 1 0;
        height: auto;
    }
    StartupScreen .actions {
        layout: horizontal;
        height: auto;
        margin-top: 1;
    }
    StartupScreen .actions Button {
        margin: 0 1;
    }
    StartupScreen .disclaimer {
        color: $text-muted;
        text-style: italic;
        text-align: center;
        margin-top: 1;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        app: BloomFolioApp = self.app  # type: ignore[assignment]

        with Container():
            yield Label("BloomFolio", classes="title")
            yield Label("Terminal Portfolio Intelligence", classes="subtitle")
            yield Static("")

            yield Static("Config Status: loaded", classes="status")
            yield Static(
                f"Ollama Status: {app.ollama_status}",
                classes="status",
                id="ollama-status",
            )
            yield Static(
                f"TradingAgents: {app.tradingagents_status}",
                classes="status",
                id="tradingagents-status",
            )

            with Vertical(classes="actions"):
                yield Button("Import CSV (i)", variant="primary", id="import-btn")
                yield Button("Help (?)", variant="default", id="help-btn")
                yield Button("Quit (q)", variant="error", id="quit-btn")

            yield Static(
                "Research & educational analysis only. Not financial advice.",
                classes="disclaimer",
            )

        yield BloomFolioFooter()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app: BloomFolioApp = self.app  # type: ignore[assignment]

        if event.button.id == "import-btn":
            app.action_import_csv()
        elif event.button.id == "help-btn":
            app.action_help()
        elif event.button.id == "quit-btn":
            import asyncio
            asyncio.create_task(app.action_quit())

    def on_mount(self) -> None:
        """Update status display on mount."""
        self.set_interval(2.0, self._refresh_status)

    def _refresh_status(self) -> None:
        """Refresh dependency status."""
        app: BloomFolioApp = self.app  # type: ignore[assignment]
        ollama = self.query_one("#ollama-status", Static)
        ta = self.query_one("#tradingagents-status", Static)
        ollama.update(f"Ollama Status: {app.ollama_status}")
        ta.update(f"TradingAgents: {app.tradingagents_status}")
