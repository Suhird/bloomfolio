"""TUI key bindings."""

from __future__ import annotations

from textual.binding import Binding

APP_BINDINGS: list[Binding] = [
    Binding("?", "help", "Help", show=True),
    Binding("q", "quit", "Quit", show=True),
    Binding("escape", "escape", "Close/Cancel", show=True),
    Binding("colon", "command_palette", "Command", show=True),
    Binding("h", "focus_left", "Left", show=False),
    Binding("j", "focus_down", "Down", show=False),
    Binding("k", "focus_up", "Up", show=False),
    Binding("l", "focus_right", "Right", show=False),
    Binding("g", "go_top", "Top", show=False),
    Binding("G", "go_bottom", "Bottom", show=False),
    Binding("slash", "search", "Search", show=False),
    Binding("r", "run_analysis", "Run", show=True),
    Binding("R", "force_refresh", "Refresh", show=True),
    Binding("i", "import_csv", "Import", show=True),
    Binding("v", "validate_csv", "Validate", show=True),
    Binding("a", "agent_monitor", "Agents", show=True),
    Binding("p", "portfolio", "Portfolio", show=True),
    Binding("t", "ticker_detail", "Ticker", show=True),
    Binding("n", "news", "News", show=False),
    Binding("s", "sentiment", "Sentiment", show=False),
    Binding("f", "fundamentals", "Fundamentals", show=False),
    Binding("T", "technicals", "Technicals", show=False),
    Binding("x", "export", "Export", show=True),
    Binding("space", "select_row", "Select", show=False),
    Binding("tab", "cycle_panels", "Next Panel", show=False),
    Binding("shift+tab", "cycle_panels_reverse", "Prev Panel", show=False),
    Binding("ctrl+c", "cancel_task", "Cancel", show=True),
    Binding("ctrl+l", "clear_logs", "Clear Logs", show=True),
]
