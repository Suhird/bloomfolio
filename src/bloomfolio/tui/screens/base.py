"""Base screen with command log and contextual footer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import Container
from textual.screen import Screen

from bloomfolio.tui.widgets.footer import BloomFolioFooter
from bloomfolio.tui.widgets.log_panel import CommandLog

if TYPE_CHECKING:
    from textual.app import ComposeResult


class BloomFolioScreen(Screen[None]):
    """Base screen that includes a bottom command log and footer."""

    DEFAULT_CSS = """
    BloomFolioScreen {
        layout: vertical;
    }
    BloomFolioScreen #content {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="content"):
            yield from self.compose_content()
        yield CommandLog()
        yield BloomFolioFooter()

    def compose_content(self) -> ComposeResult:
        """Subclasses override this instead of compose."""
        yield from ()

    def log_ui(self, message: str) -> None:
        """Write a message to the bottom command log."""
        try:
            log = self.query_one(CommandLog)
            log.write_line(message)
        except Exception:
            pass
