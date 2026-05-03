"""Footer widget showing active shortcuts."""

from __future__ import annotations

from textual.widgets import Footer


class BloomFolioFooter(Footer):
    """Custom footer with Bloomberg-inspired styling."""

    DEFAULT_CSS = """
    BloomFolioFooter {
        background: $surface;
        color: $text;
        height: 1;
    }
    BloomFolioFooter > .footer--key {
        background: $primary;
        color: $background;
        text-style: bold;
    }
    BloomFolioFooter > .footer--highlight-key {
        background: $primary;
        color: $background;
        text-style: bold;
    }
    BloomFolioFooter > .footer--highlight {
        background: $surface;
    }
    """

    def __init__(self) -> None:
        super().__init__()
