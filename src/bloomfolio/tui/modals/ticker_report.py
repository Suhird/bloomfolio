"""Ticker analysis report modal."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.binding import Binding
from textual.containers import Grid, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from bloomfolio.domain.reports import TickerAnalysisResult


class TickerReportModal(ModalScreen[None]):
    """Modal that displays a single ticker's analysis report."""

    BINDINGS = [
        Binding("q", "quit", "Close", show=False),
        Binding("escape", "escape", "Close", show=False),
    ]

    DEFAULT_CSS = """
    TickerReportModal {
        align: center middle;
    }
    TickerReportModal > Grid {
        width: 90;
        height: 85%;
        border: thick $primary;
        background: $surface;
        grid-size: 1;
        grid-rows: 1fr auto;
    }
    TickerReportModal > Grid > VerticalScroll {
        height: 1fr;
        padding: 1 2;
    }
    TickerReportModal > Grid > VerticalScroll > Static {
        height: auto;
        width: 100%;
    }
    TickerReportModal > Grid > Button {
        width: 100%;
    }
    """

    def __init__(self, ticker: str, result: TickerAnalysisResult) -> None:
        super().__init__()
        self.ticker = ticker
        self.result = result

    def compose(self) -> ComposeResult:
        with Grid():
            with VerticalScroll():
                yield Static(self._build_content(), markup=True)
            yield Button("Close (q)", variant="primary", id="close")

    def _build_content(self) -> str:
        lines: list[str] = [f"[b]{self.ticker} Analysis[/b]\n"]
        if self.result.decision:
            d = self.result.decision
            lines.append(
                f"Rating: [b]{d.rating}[/b]  |  "
                f"Action: {d.action_label}  |  "
                f"Confidence: {d.confidence:.0%}"
            )
            if d.thesis:
                lines.append(f"\nThesis: {d.thesis}")
            if d.bull_case:
                lines.append(f"\nBull: {d.bull_case}")
            if d.bear_case:
                lines.append(f"\nBear: {d.bear_case}")
            if d.risk_notes:
                lines.append(f"\nRisks: {'; '.join(d.risk_notes)}")
        else:
            lines.append("No decision generated.")

        if self.result.reports:
            lines.append(
                f"\n[b]Agent Reports ({len(self.result.reports)} stages):[/b]"
            )
            for report in self.result.reports:
                lines.append(
                    f"\n[b]{report.agent_name}[/b] — {report.summary[:200]}..."
                )

        if self.result.errors:
            lines.append(f"\n[red]Errors: {', '.join(self.result.errors)}[/red]")

        return "\n".join(lines)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.dismiss()

    def action_quit(self) -> None:
        self.dismiss()

    def action_escape(self) -> None:
        self.dismiss()
