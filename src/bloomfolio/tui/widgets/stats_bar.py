"""Footer stats bar widget."""

from __future__ import annotations

from textual.widgets import Static


class StatsBar(Static):
    """Bottom status bar with live statistics."""

    DEFAULT_CSS = """
    StatsBar {
        height: 1;
        background: $surface;
        color: $text;
        border-top: solid $border;
        padding: 0 2;
        content-align: center middle;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.llm_calls = 0
        self.tool_calls = 0
        self.tickers_total = 0
        self.tickers_done = 0
        self.elapsed_seconds = 0
        self.provider = "-"

    def update_stats(
        self,
        *,
        llm_calls: int | None = None,
        tool_calls: int | None = None,
        tickers_total: int | None = None,
        tickers_done: int | None = None,
        elapsed_seconds: int | None = None,
        provider: str | None = None,
    ) -> None:
        """Update one or more stat values."""
        if llm_calls is not None:
            self.llm_calls = llm_calls
        if tool_calls is not None:
            self.tool_calls = tool_calls
        if tickers_total is not None:
            self.tickers_total = tickers_total
        if tickers_done is not None:
            self.tickers_done = tickers_done
        if elapsed_seconds is not None:
            self.elapsed_seconds = elapsed_seconds
        if provider is not None:
            self.provider = provider
        self._refresh_display()

    def on_mount(self) -> None:
        self._refresh_display()

    def _refresh_display(self) -> None:
        parts: list[str] = [f"Provider: [b]{self.provider}[/b]"]
        if self.tickers_total > 0:
            parts.append(f"Tickers: [b]{self.tickers_done}/{self.tickers_total}[/b]")
        if self.llm_calls > 0:
            parts.append(f"LLM: [b]{self.llm_calls}[/b]")
        if self.tool_calls > 0:
            parts.append(f"Tools: [b]{self.tool_calls}[/b]")
        if self.elapsed_seconds > 0:
            mins = self.elapsed_seconds // 60
            secs = self.elapsed_seconds % 60
            parts.append(f"⏱ [b]{mins:02d}:{secs:02d}[/b]")
        self.update("  |  ".join(parts))
