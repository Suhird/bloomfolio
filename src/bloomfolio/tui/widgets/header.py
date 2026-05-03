"""Dashboard header widget."""

from __future__ import annotations

from textual.widgets import Static


class BloomFolioHeader(Static):
    """Top header bar with title and contextual shortcuts."""

    DEFAULT_CSS = """
    BloomFolioHeader {
        height: 3;
        background: $surface;
        color: $text;
        border-bottom: solid $border;
        padding: 0 2;
        content-align: center middle;
    }
    BloomFolioHeader .title {
        text-style: bold;
        color: $primary;
    }
    BloomFolioHeader .shortcuts {
        color: $text-muted;
    }
    """

    def __init__(self, title: str = "BloomFolio", shortcuts: str = "") -> None:
        super().__init__()
        self._title = title
        self._shortcuts = shortcuts

    def on_mount(self) -> None:
        self._refresh_display()

    def set_context(self, title: str, shortcuts: str) -> None:
        """Update header context."""
        self._title = title
        self._shortcuts = shortcuts
        self._refresh_display()

    def _refresh_display(self) -> None:
        text = f"[b]{self._title}[/b]"
        if self._shortcuts:
            text += f"    [dim]{self._shortcuts}[/dim]"
        self.update(text)
