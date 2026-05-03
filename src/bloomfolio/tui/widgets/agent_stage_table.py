"""Agent stage progress table widget — TradingAgents team layout."""

from __future__ import annotations

from textual.widgets import Static

STAGE_LABELS: dict[str, str] = {
    "fundamental": "Fundamental",
    "technical": "Technical",
    "news": "News",
    "sentiment": "Sentiment",
    "bull": "Bull Research",
    "bear": "Bear Research",
    "trader": "Trader",
    "risk": "Risk Review",
    "portfolio_manager": "Portfolio Mgr",
}

TEAMS: list[tuple[str, list[str]]] = [
    ("Analyst Team", ["fundamental", "technical", "news", "sentiment"]),
    ("Research Team", ["bull", "bear"]),
    ("Trading Team", ["trader"]),
    ("Risk Mgmt", ["risk"]),
    ("Portfolio Mgmt", ["portfolio_manager"]),
]

STATUS_ICONS: dict[str, str] = {
    "pending": "⏳",
    "in_progress": "🔄",
    "completed": "✅",
    "error": "❌",
}

STATUS_COLORS: dict[str, str] = {
    "pending": "dim",
    "in_progress": "cyan",
    "completed": "green",
    "error": "red",
}


class AgentStageTable(Static):
    """Table showing per-team analysis status."""

    DEFAULT_CSS = """
    AgentStageTable {
        height: 100%;
        padding: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._status: dict[str, str] = dict.fromkeys(STAGE_LABELS.keys(), "pending")
        self._current_ticker: str | None = None

    def reset(self) -> None:
        """Reset all stages to pending."""
        self._status = dict.fromkeys(STAGE_LABELS.keys(), "pending")
        self._current_ticker = None
        self._refresh_display()

    def set_stage_status(self, stage: str, status: str) -> None:
        """Update a single stage status."""
        if stage in self._status:
            self._status[stage] = status
            self._refresh_display()

    def set_current_ticker(self, ticker: str) -> None:
        """Show which ticker is currently being analyzed."""
        self._current_ticker = ticker
        self._refresh_display()

    def on_mount(self) -> None:
        self._refresh_display()

    def _refresh_display(self) -> None:
        lines: list[str] = []
        if self._current_ticker:
            lines.append(f"[b]Active: {self._current_ticker}[/b]\n")

        for team_name, stages in TEAMS:
            lines.append(f"[b]{team_name}[/b]")
            for stage in stages:
                label = STAGE_LABELS.get(stage, stage)
                status = self._status.get(stage, "pending")
                icon = STATUS_ICONS.get(status, "⏳")
                color = STATUS_COLORS.get(status, "white")
                lines.append(f"  [{color}]{icon} {label}[/{color}]")
            lines.append("")

        self.update("\n".join(lines))
