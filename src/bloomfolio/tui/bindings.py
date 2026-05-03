"""TUI key bindings."""

from __future__ import annotations

from textual.binding import Binding

APP_BINDINGS: list[Binding] = [
    # All app-level bindings are hidden from the footer;
    # each screen exposes only its own contextual bindings.
    Binding("?", "help", "Help", show=False),
    Binding("q", "quit", "Quit", show=False),
    Binding("escape", "escape", "Close/Cancel", show=False),
    Binding("colon", "command_palette", "Command", show=False),
    Binding("h", "focus_left", "Left", show=False),
    Binding("j", "focus_down", "Down", show=False),
    Binding("k", "focus_up", "Up", show=False),
    Binding("l", "focus_right", "Right", show=False),
    Binding("g", "go_top", "Top", show=False),
    Binding("G", "go_bottom", "Bottom", show=False),
    Binding("slash", "search", "Search", show=False),
    Binding("r", "run_analysis", "Run", show=False),
    Binding("R", "force_refresh", "Refresh", show=False),
    Binding("i", "import_csv", "Import", show=False),
    Binding("v", "validate_csv", "Validate", show=False),
    Binding("a", "agent_monitor", "Agents", show=False),
    Binding("p", "portfolio", "Portfolio", show=False),
    Binding("t", "ticker_detail", "Ticker", show=False),
    Binding("n", "news", "News", show=False),
    Binding("s", "sentiment", "Sentiment", show=False),
    Binding("f", "fundamentals", "Fundamentals", show=False),
    Binding("T", "technicals", "Technicals", show=False),
    Binding("x", "export", "Export", show=False),
    Binding("space", "select_row", "Select", show=False),
    Binding("tab", "cycle_panels", "Next Panel", show=False),
    Binding("shift+tab", "cycle_panels_reverse", "Prev Panel", show=False),
    Binding("ctrl+c", "cancel_task", "Cancel", show=False),
    Binding("ctrl+l", "clear_logs", "Clear Logs", show=False),
]
