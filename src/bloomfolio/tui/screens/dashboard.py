"""Main dashboard screen — TradingAgents-inspired persistent layout."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen

from bloomfolio.agents.runner import AnalysisRunner
from bloomfolio.tui.widgets.agent_stage_table import AgentStageTable
from bloomfolio.tui.widgets.header import BloomFolioHeader
from bloomfolio.tui.widgets.holdings_table import HoldingsTable
from bloomfolio.tui.widgets.message_stream import MessageStream
from bloomfolio.tui.widgets.report_viewer import ReportViewer
from bloomfolio.tui.widgets.stats_bar import StatsBar

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from bloomfolio.domain.portfolio import Portfolio
    from bloomfolio.domain.reports import TickerAnalysisResult
    from bloomfolio.tui.app import BloomFolioApp


class DashboardScreen(Screen[None]):
    """Persistent dashboard — upper: holdings + messages, lower: report/progress."""

    BINDINGS = [
        Binding("i", "import_csv", "Import", show=True),
        Binding("r", "run_analysis", "Run", show=True),
        Binding("t", "show_ticker_detail", "Detail", show=True),
        Binding("x", "export", "Export", show=True),
        Binding("?", "help", "Help", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+c", "cancel_analysis", "Cancel", show=False),
        Binding("ctrl+equal", "increase_detail", "+", show=False),
        Binding("ctrl+minus", "decrease_detail", "-", show=False),
    ]

    DEFAULT_CSS = """
    DashboardScreen {
        layout: vertical;
    }
    DashboardScreen #main {
        height: 1fr;
        layout: vertical;
    }
    DashboardScreen #upper {
        height: 40%;
        layout: horizontal;
    }
    DashboardScreen #lower {
        height: 60%;
        layout: horizontal;
    }
    DashboardScreen .panel {
        height: 100%;
        border: solid $border;
    }
    """

    is_analyzing: reactive[bool] = reactive(False)
    detail_ratio: reactive[int] = reactive(40)  # percentage for upper panel
    selected_ticker: reactive[str | None] = reactive(None)

    def __init__(self) -> None:
        super().__init__()
        self.runner: AnalysisRunner | None = None
        self._analysis_task: asyncio.Task[None] | None = None
        self._elapsed_task: asyncio.Task[None] | None = None
        self._start_time: float = 0.0

    def compose(self) -> ComposeResult:
        yield BloomFolioHeader(
            title="BloomFolio",
            shortcuts="[i] Import  [r] Run  [t] Detail  [x] Export  [?] Help  [q] Quit",
        )

        with Container(id="main"):
            with Horizontal(id="upper"):
                with Vertical(classes="panel"):
                    yield HoldingsTable()
                with Vertical(classes="panel"):
                    yield MessageStream()

            with Horizontal(id="lower"):
                yield ReportViewer()

        yield StatsBar()

    def on_mount(self) -> None:
        """Initialize dashboard state."""
        self._refresh_holdings()
        self._refresh_detail_placeholder()
        self._update_stats_bar()

    # ── Reactive watchers ──

    def watch_is_analyzing(self, analyzing: bool) -> None:
        """Swap lower panel between report viewer and agent progress."""
        lower = self.query_one("#lower", Horizontal)
        for child in list(lower.children):
            child.remove()
        if analyzing:
            lower.mount(AgentStageTable())
            header = self.query_one(BloomFolioHeader)
            header.set_context(
                "Analysis Running",
                "[Ctrl+C] Cancel  [q] Back  [?] Help",
            )
        else:
            lower.mount(ReportViewer())
            header = self.query_one(BloomFolioHeader)
            header.set_context(
                "BloomFolio",
                "[i] Import  [r] Run  [t] Detail  [x] Export  [?] Help  [q] Quit",
            )
            # Refresh detail view now that report viewer is back
            self._refresh_detail_view()

    def watch_detail_ratio(self, ratio: int) -> None:
        """Adjust upper/lower split."""
        upper = self.query_one("#upper", Horizontal)
        lower = self.query_one("#lower", Horizontal)
        upper.styles.height = f"{ratio}%"
        lower.styles.height = f"{100 - ratio}%"

    def watch_selected_ticker(self, ticker: str | None) -> None:
        """Update report viewer when ticker selection changes."""
        self._refresh_detail_view()

    # ── Actions ──

    def action_increase_detail(self) -> None:
        """Grow the upper panel."""
        self.detail_ratio = min(70, self.detail_ratio + 10)

    def action_decrease_detail(self) -> None:
        """Shrink the upper panel."""
        self.detail_ratio = max(20, self.detail_ratio - 10)

    def action_run_analysis(self) -> None:
        """Start portfolio analysis."""
        app: BloomFolioApp = self.app  # type: ignore[assignment]
        portfolio: Portfolio | None = app.current_portfolio

        if portfolio is None:
            self._push_system("No portfolio loaded. Press 'i' to import.")
            return

        if self.is_analyzing:
            self._push_system("Analysis already running.")
            return

        self.is_analyzing = True
        self.runner = AnalysisRunner()
        self._start_time = asyncio.get_event_loop().time()

        # Reset stage table
        try:
            stage_table = self.query_one(AgentStageTable)
            stage_table.reset()
        except Exception:
            pass

        self._elapsed_task = asyncio.create_task(self._tick_elapsed())

        task = asyncio.create_task(self._run_analysis(portfolio))
        task.add_done_callback(self._on_analysis_done)
        self._analysis_task = task

        tickers = portfolio.get_tickers()
        estimated = len(tickers) * 9
        self._push_system(
            f"Starting analysis: {len(tickers)} tickers (~{estimated} LLM calls, 2 concurrent)"
        )

    def action_cancel_analysis(self) -> None:
        """Cancel running analysis."""
        if self.runner:
            self.runner.cancel()
        if self._analysis_task:
            self._analysis_task.cancel()
        self.is_analyzing = False
        self._push_system("Analysis cancelled.")
        self._stop_elapsed_timer()

    def action_show_ticker_detail(self) -> None:
        """Show detail for selected ticker."""
        table = self.query_one(HoldingsTable)
        ticker = table.get_selected_ticker()
        if not ticker:
            self._push_system("Select a ticker first (use ↑/↓).")
            return

        app: BloomFolioApp = self.app  # type: ignore[assignment]
        results: dict[str, TickerAnalysisResult] = getattr(app, "analysis_results", {})
        result = results.get(ticker)

        if not result:
            self._push_system(
                f"No analysis available for {ticker}. Press 'r' to run analysis."
            )
            return

        # Always try to show something visible.
        # During analysis the lower panel is AgentStageTable, so pop a modal.
        # When idle update the lower panel; fall back to modal if it is missing.
        if self.is_analyzing:
            self._push_system(f"Opening {ticker} report (modal)...")
            self._push_ticker_modal(ticker, result)
            return

        # Not analyzing — try lower panel first
        try:
            self.selected_ticker = ticker
            self._push_system(f"Showing {ticker} report in panel.")
        except Exception as e:
            self._push_system(f"Panel unavailable, opening modal: {e}")
            self._push_ticker_modal(ticker, result)

    def _push_ticker_modal(self, ticker: str, result: TickerAnalysisResult) -> None:
        """Push the ticker report modal, surfacing any error."""
        try:
            from bloomfolio.tui.modals.ticker_report import TickerReportModal

            self.app.push_screen(TickerReportModal(ticker, result))
        except Exception as e:
            self._push_error(f"Failed to open report modal: {e}")

    def action_import_csv(self) -> None:
        """Open import modal."""
        from bloomfolio.tui.screens.import_portfolio import ImportPortfolioScreen

        self.app.push_screen(ImportPortfolioScreen())

    def action_export(self) -> None:
        """Open export modal."""
        app: BloomFolioApp = self.app  # type: ignore[assignment]
        if app.current_portfolio is None:
            self._push_system("No portfolio to export.")
            return
        from bloomfolio.tui.screens.export import ExportScreen

        self.app.push_screen(ExportScreen(app.current_portfolio))

    # ── Data refresh ──

    def _refresh_holdings(self) -> None:
        """Reload holdings table from app state."""
        app: BloomFolioApp = self.app  # type: ignore[assignment]
        table = self.query_one(HoldingsTable)
        results: dict[str, TickerAnalysisResult] = getattr(app, "analysis_results", {})
        table.load_portfolio(app.current_portfolio, results)
        self._update_stats_bar()

    def _refresh_detail_placeholder(self) -> None:
        """Show placeholder in report viewer."""
        try:
            viewer = self.query_one(ReportViewer)
        except Exception:
            return
        app: BloomFolioApp = self.app  # type: ignore[assignment]
        if app.current_portfolio is None:
            viewer.show_placeholder("Press 'i' to import your portfolio.")
        else:
            viewer.show_placeholder(
                "Select a ticker and press 't' to view analysis.\n"
                "Press 'r' to start multi-agent analysis."
            )

    def _refresh_detail_view(self) -> None:
        """Show analysis detail for selected ticker."""
        try:
            viewer = self.query_one(ReportViewer)
        except Exception:
            return
        ticker = self.selected_ticker
        if not ticker:
            self._refresh_detail_placeholder()
            return

        app: BloomFolioApp = self.app  # type: ignore[assignment]
        results: dict[str, TickerAnalysisResult] = getattr(app, "analysis_results", {})
        result = results.get(ticker)

        if not result:
            viewer.show_placeholder(
                f"No analysis available for {ticker}. Press 'r' to run analysis."
            )
            return

        lines: list[str] = []
        if result.decision:
            d = result.decision
            lines.append(
                f"Rating: [b]{d.rating}[/b]  |  Action: {d.action_label}  |  Confidence: {d.confidence:.0%}"
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

        if result.reports:
            lines.append(f"\n[b]Agent Reports ({len(result.reports)} stages):[/b]")
            for report in result.reports:
                lines.append(
                    f"\n[b]{report.agent_name}[/b] — {report.summary[:120]}..."
                )

        if result.errors:
            lines.append(f"\n[red]Errors: {', '.join(result.errors)}[/red]")

        viewer.show_report(f"{ticker} Analysis", "\n".join(lines))

    def _update_stats_bar(self) -> None:
        """Sync stats bar with app state."""
        app: BloomFolioApp = self.app  # type: ignore[assignment]
        bar = self.query_one(StatsBar)
        portfolio = app.current_portfolio
        results: dict[str, TickerAnalysisResult] = getattr(app, "analysis_results", {})
        tickers_total = len(portfolio.get_tickers()) if portfolio else 0
        tickers_done = sum(1 for r in results.values() if r.decision or r.reports)
        bar.update_stats(
            provider=app.settings.llm_provider,
            tickers_total=tickers_total,
            tickers_done=tickers_done,
        )

    # ── Analysis runner ──

    async def _run_analysis(self, portfolio: Portfolio) -> None:
        """Run analysis and wire progress to widgets."""
        if self.runner is None:
            return

        app: BloomFolioApp = self.app  # type: ignore[assignment]
        bar = self.query_one(StatsBar)
        llm_count = 0

        async def progress_callback(ticker: str, stage: str) -> None:
            self._push_message(f"{ticker} → {stage}")
            if stage == "complete":
                bar.update_stats(tickers_done=bar.tickers_done + 1)
            else:
                try:
                    stage_table = self.query_one(AgentStageTable)
                    stage_table.set_stage_status(stage, "in_progress")
                    stage_table.set_current_ticker(ticker)
                except Exception:
                    pass
            nonlocal llm_count
            llm_count += 1
            bar.update_stats(llm_calls=llm_count)

        async def result_callback(ticker: str, result: TickerAnalysisResult) -> None:
            """Update app state incrementally as each ticker finishes."""
            current: dict[str, TickerAnalysisResult] = dict(app.analysis_results)
            current[ticker] = result
            app.analysis_results = current
            self._push_system(f"{ticker} analysis complete")

        try:
            results = await self.runner.run_portfolio_analysis(
                portfolio,
                progress_callback=progress_callback,
                result_callback=result_callback,
            )
            app.analysis_results = results
            self._push_system(f"Analysis complete: {len(results)} tickers.")
        except asyncio.CancelledError:
            self._push_system("Analysis cancelled.")
        except Exception as e:
            self._push_error(f"Analysis failed: {e}")

    def _on_analysis_done(self, task: asyncio.Task[None]) -> None:
        """Cleanup after analysis finishes."""
        try:
            task.result()
        except asyncio.CancelledError:
            self._push_system("Analysis task cancelled.")
        except Exception as e:
            self._push_error(f"Analysis task error: {e}")
        self.is_analyzing = False
        self._stop_elapsed_timer()
        self._refresh_holdings()
        self._update_stats_bar()

    async def _tick_elapsed(self) -> None:
        """Update elapsed time in footer every second."""
        bar = self.query_one(StatsBar)
        while self.is_analyzing:
            elapsed = int(asyncio.get_event_loop().time() - self._start_time)
            bar.update_stats(elapsed_seconds=elapsed)
            await asyncio.sleep(1)

    def _stop_elapsed_timer(self) -> None:
        """Stop the elapsed timer."""
        if self._elapsed_task:
            self._elapsed_task.cancel()
            self._elapsed_task = None

    # ── Message helpers ──

    def _push_message(self, text: str) -> None:
        try:
            stream = self.query_one(MessageStream)
            stream.push(text)
        except Exception:
            pass

    def _push_system(self, text: str) -> None:
        try:
            stream = self.query_one(MessageStream)
            stream.push_system(text)
        except Exception:
            pass

    def _push_error(self, text: str) -> None:
        try:
            stream = self.query_one(MessageStream)
            stream.push_error(text)
        except Exception:
            pass

    # ── App state watchers ──

    def watch_current_portfolio(self) -> None:
        """React to portfolio import (called by app when reactive changes)."""
        self._refresh_holdings()
        self._refresh_detail_placeholder()
        self._update_stats_bar()

    def watch_analysis_results(self) -> None:
        """React to analysis completion."""
        self._refresh_holdings()
        self._refresh_detail_view()
        self._update_stats_bar()
