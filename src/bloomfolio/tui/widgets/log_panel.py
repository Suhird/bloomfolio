"""Bottom log panel widget for TUI."""

from __future__ import annotations

from textual.widgets import RichLog


class CommandLog(RichLog):
    """Small terminal-like log panel shown at the bottom of every screen."""

    DEFAULT_CSS = """
    CommandLog {
        height: 5;
        border-top: solid $border;
        background: $surface-darken-1;
        color: $text;
        padding: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__(highlight=True, wrap=True, id="command-log")

    def write_line(self, text: str) -> None:
        """Write a line to the log."""
        self.write(text + "\n")
