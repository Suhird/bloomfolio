"""Agent monitor screen."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Label, Log, ProgressBar, Static

from bloomfolio.agents.runner import AnalysisRunner
from bloomfolio.tui.widgets.footer import BloomFolioFooter

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from bloomfolio.domain.portfolio import Portfolio


class AgentMonitorScreen(Screen[None]):
    """Agent run monitor screen."""

    DEFAULT_CSS = """
    AgentMonitorScreen {
        layout: vertical;
    }
    AgentMonitorScreen > Container {
        height: 1fr;
        layout: horizontal;
    }
    AgentMonitorScreen .panel {
        width: 1fr;
        height: 100%;
        border: solid $border;
        padding: 1;
    }
    AgentMonitorScreen .panel-title {
        text-style: bold;
        color: $primary;
        height: auto;
    }
    """

    def __init__(self, portfolio: Portfolio) -> None:
        super().__init__()
        self.portfolio = portfolio
        self.runner = AnalysisRunner()

    def compose(self) -> ComposeResult:
        with Container():
            with Vertical(classes="panel"):
                yield Label("Agent Progress", classes="panel-title")
                yield ProgressBar(id="overall-progress", total=len(self.portfolio.get_tickers()))
                yield Static("Queue: " + ", ".join(self.portfolio.get_tickers()), id="queue")
                yield Static("Active: -", id="active")
                yield Static("Stage: -", id="stage")
                yield Static("Validation: -", id="validation")

            with Vertical(classes="panel"):
                yield Label("Logs", classes="panel-title")
                log = Log(id="agent-log")
                yield log

        yield BloomFolioFooter()

    def on_mount(self) -> None:
        """Start analysis on mount."""
        asyncio.create_task(self._run_analysis())

    async def _run_analysis(self) -> None:
        """Run analysis for all tickers."""
        log = self.query_one("#agent-log", Log)
        progress = self.query_one("#overall-progress", ProgressBar)
        active = self.query_one("#active", Static)
        stage_label = self.query_one("#stage", Static)
        validation = self.query_one("#validation", Static)

        tickers = self.portfolio.get_tickers()
        log.write_line(f"Starting analysis for {len(tickers)} tickers...")

        async def progress_callback(ticker: str, stage: str) -> None:
            active.update(f"Active: {ticker}")
            stage_label.update(f"Stage: {stage}")
            log.write_line(f"  {ticker} -> {stage}")
            if stage == "complete":
                progress.advance(1)
                validation.update("Validation: ok")

        try:
            results = await self.runner.run_portfolio_analysis(
                self.portfolio,
                progress_callback=progress_callback,
            )
            self.app.analysis_results = results  # type: ignore[attr-defined]
            log.write_line(f"Analysis complete. {len(results)} tickers analyzed.")
        except Exception as e:
            log.write_line(f"Analysis failed: {e}")
            validation.update(f"Validation: error - {e}")

        active.update("Active: -")
        stage_label.update("Stage: complete")
