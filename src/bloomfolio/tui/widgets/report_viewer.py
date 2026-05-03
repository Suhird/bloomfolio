"""Report viewer widget for rendering analysis output."""

from __future__ import annotations

from textual.widgets import Static


class ReportViewer(Static):
    """Panel that displays markdown-like analysis output."""

    DEFAULT_CSS = """
    ReportViewer {
        height: 100%;
        border: solid $border;
        background: $surface;
        padding: 1 2;
        overflow-y: auto;
    }
    ReportViewer .placeholder {
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._content: str = ""

    def show_placeholder(self, text: str) -> None:
        """Show placeholder text when no report is selected."""
        self._content = text
        self.update(f"[dim]{text}[/dim]")

    def show_report(self, title: str, content: str) -> None:
        """Display a report with title."""
        self._content = content
        self.update(f"[b]{title}[/b]\n\n{content}")

    def clear(self) -> None:
        """Clear the viewer."""
        self._content = ""
        self.update("")
