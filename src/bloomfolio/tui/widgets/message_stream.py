"""Live message stream widget with timestamps."""

from __future__ import annotations

import datetime

from textual.widgets import RichLog


class MessageStream(RichLog):
    """Scrollable message stream with timestamps."""

    DEFAULT_CSS = """
    MessageStream {
        height: 100%;
        border: solid $border;
        background: $surface-darken-1;
        padding: 0 1;
    }
    """

    def __init__(self, id: str | None = None) -> None:  # noqa: A002
        super().__init__(highlight=True, wrap=True, id=id)

    def push(self, message: str) -> None:
        """Append a message line with timestamp."""
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.write(f"[{ts}] {message}\n")

    def push_system(self, message: str) -> None:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.write(f"[{ts}] [cyan][system][/cyan] {message}\n")

    def push_agent(self, agent: str, message: str) -> None:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.write(f"[{ts}] [green][{agent}][/green] {message}\n")

    def push_tool(self, tool: str, args: str) -> None:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.write(f"[{ts}] [yellow][tool][/yellow] {tool}({args})\n")

    def push_error(self, message: str) -> None:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.write(f"[{ts}] [red][error][/red] {message}\n")
