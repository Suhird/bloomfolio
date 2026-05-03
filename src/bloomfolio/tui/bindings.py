"""TUI key bindings."""

from __future__ import annotations

from textual.binding import Binding

# App-level bindings that are always active.
# Dashboard-specific bindings (i, r, t, x, q, ?) live in DashboardScreen.BINDINGS.
APP_BINDINGS: list[Binding] = [
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
    Binding("space", "select_row", "Select", show=False),
    Binding("tab", "cycle_panels", "Next Panel", show=False),
    Binding("shift+tab", "cycle_panels_reverse", "Prev Panel", show=False),
]
