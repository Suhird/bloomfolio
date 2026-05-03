"""Agent monitor screen."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Label, ProgressBar, RichLog, Static

from bloomfolio.agents.runner import AnalysisRunner
from bloomfolio.llm.client import LLMGateway
from bloomfolio.tui.screens.base import BloomFolioScreen

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from bloomfolio.domain.portfolio import Portfolio


class AgentMonitorScreen(BloomFolioScreen):
    """Agent run monitor screen."""

    BINDINGS = [
        Binding("q", "quit", "Back", show=True),
        Binding("escape", "escape", "Back", show=True),
        Binding("ctrl+c", "cancel_task", "Cancel", show=True),
    ]

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

    def compose_content(self) -> ComposeResult:
        with Container():
            with Vertical(classes="panel"):
                yield Label("Agent Progress", classes="panel-title")
                yield ProgressBar(id="overall-progress", total=len(self.portfolio.get_tickers()))
                yield Static("Queue: " + ", ".join(self.portfolio.get_tickers()), id="queue")
                yield Static("Active: -", id="active")
                yield Static("Stage: -", id="stage")
                yield Static("Status: Waiting...", id="validation")

            with Vertical(classes="panel"):
                yield Label("Logs", classes="panel-title")
                log = RichLog(id="agent-log", highlight=True)
                yield log

    def on_mount(self) -> None:
        """Start analysis on mount."""
        task = asyncio.create_task(self._run_analysis())
        task.add_done_callback(self._on_analysis_done)

    def action_cancel_task(self) -> None:
        """Cancel the running analysis."""
        self.runner.cancel()
        self.log_ui("[yellow]Cancel requested[/yellow]")
        try:
            status = self.query_one("#validation", Static)
            status.update("Status: cancelling...")
        except Exception:
            pass

    def _on_analysis_done(self, task: asyncio.Task[None]) -> None:
        """Handle analysis task completion and surface unhandled exceptions."""
        try:
            task.result()
        except asyncio.CancelledError:
            self._safe_log("[yellow]Analysis cancelled.[/yellow]")
            self._safe_status("Status: cancelled")
        except Exception as e:
            self._safe_log(f"[red]Unhandled error: {e}[/red]")
            self._safe_status(f"Status: crashed - {e}")

    def _safe_log(self, message: str) -> None:
        """Write to the internal log, swallowing DOM errors if screen was popped."""
        try:
            log = self.query_one("#agent-log", RichLog)
            log.write(message)
        except Exception:
            pass
        self.log_ui(message)

    def _safe_status(self, message: str) -> None:
        """Update status label, swallowing DOM errors if screen was popped."""
        try:
            status = self.query_one("#validation", Static)
            status.update(message)
        except Exception:
            pass

    async def _run_analysis(self) -> None:
        """Run analysis for all tickers."""
        log = self.query_one("#agent-log", RichLog)
        progress = self.query_one("#overall-progress", ProgressBar)
        active = self.query_one("#active", Static)
        stage_label = self.query_one("#stage", Static)
        status = self.query_one("#validation", Static)

        tickers = self.portfolio.get_tickers()
        num_stages = 9  # per ticker in fallback graph
        estimated = len(tickers) * num_stages

        log.write(f"Starting analysis for [b]{len(tickers)}[/b] tickers...")
        log.write(
            f"[dim]~{estimated} LLM calls total. Each may take 10-60s. "
            f"Progress bar advances once per ticker.[/dim]"
        )
        self.log_ui(f"Analysis started: {len(tickers)} tickers, ~{estimated} stages")

        if not tickers:
            log.write("[yellow]No tickers to analyze (portfolio may contain only cash).[/yellow]")
            status.update("Status: no tickers")
            return

        # Pre-flight model check
        status.update("Status: checking model...")
        llm = LLMGateway()
        model_ok = await llm.check_model_available()
        if not model_ok:
            model_name = llm._get_model_name()
            log.write(
                f"[red]Model '{model_name}' is not available in Ollama.[/red]\n"
                f"Run: [b]ollama pull {model_name}[/b]"
            )
            status.update(f"Status: model missing ({model_name})")
            self.log_ui(f"[red]Model missing: {model_name}[/red]")
            return

        log.write(f"Model [b]{llm._get_model_name()}[/b] is available.")
        status.update("Status: running")
        self.log_ui(f"Model {llm._get_model_name()} available — running")

        async def progress_callback(ticker: str, stage: str) -> None:
            active.update(f"Active: {ticker}")
            stage_label.update(f"Stage: {stage}")
            if stage == "complete":
                progress.advance(1)
                log.write(f"[green]{ticker} -> complete[/green]")
                self.log_ui(f"[green]{ticker} complete[/green]")
            else:
                msg = f"  {ticker} -> {stage}"
                log.write(msg)
                self.log_ui(msg)

        try:
            results = await self.runner.run_portfolio_analysis(
                self.portfolio,
                progress_callback=progress_callback,
            )
            self.app.analysis_results = results  # type: ignore[attr-defined]

            error_count = sum(1 for r in results.values() if r.errors)
            if error_count:
                log.write(
                    f"[yellow]Analysis finished with {error_count}/{len(results)} "
                    f"tickers reporting errors.[/yellow]"
                )
                self.log_ui(
                    f"[yellow]Done with {error_count}/{len(results)} errors[/yellow]"
                )
                for ticker, result in results.items():
                    if result.errors:
                        log.write(f"[red]  {ticker}: {result.errors[0]}[/red]")
            else:
                log.write(
                    f"[green]Analysis complete. {len(results)} tickers analyzed.[/green]"
                )
                self.log_ui(
                    f"[green]Analysis complete: {len(results)} tickers[/green]"
                )
            status.update("Status: done")
        except asyncio.CancelledError:
            log.write("[yellow]Analysis cancelled by user.[/yellow]")
            self.log_ui("[yellow]Analysis cancelled[/yellow]")
            status.update("Status: cancelled")
        except Exception as e:
            log.write(f"[red]Analysis failed: {e}[/red]")
            self.log_ui(f"[red]Analysis failed: {e}[/red]")
            status.update(f"Status: error - {e}")

        active.update("Active: -")
        stage_label.update("Stage: complete")
