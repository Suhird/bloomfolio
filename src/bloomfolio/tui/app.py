"""Main TUI application."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from textual.app import App
from textual.binding import Binding
from textual.reactive import reactive

from bloomfolio.config.settings import get_settings
from bloomfolio.observability.logging import configure_logging, get_logger
from bloomfolio.tui.bindings import APP_BINDINGS
from bloomfolio.tui.modals.help import HelpModal
from bloomfolio.tui.modals.schema_help import SchemaHelpModal
from bloomfolio.tui.screens.startup import StartupScreen
from bloomfolio.tui.theme import BLOOMFOLIO_THEME

if TYPE_CHECKING:
    from bloomfolio.domain.portfolio import Portfolio

logger = get_logger(__name__)


class BloomFolioApp(App[None]):
    """BloomFolio terminal application."""

    CSS = """
    Screen {
        background: $background;
        color: $text;
    }
    """

    BINDINGS = [
        Binding(b.key, b.action, b.description, show=b.show)
        for b in APP_BINDINGS
    ]
    TITLE = "BloomFolio"
    SUB_TITLE = "Terminal Portfolio Intelligence"

    current_portfolio: reactive[Portfolio | None] = reactive(None)
    ollama_status: reactive[str] = reactive("checking...")
    tradingagents_status: reactive[str] = reactive("checking...")

    def __init__(self) -> None:
        super().__init__()
        self.settings = get_settings()
        self.analysis_results: dict[str, Any] = {}
        configure_logging()
        logger.info("bloomfolio_app_initializing")

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.register_theme(BLOOMFOLIO_THEME)
        self.theme = "bloomfolio"
        self.push_screen(StartupScreen())
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Check Ollama and TradingAgents status asynchronously."""
        import asyncio

        async def check() -> None:
            await self._check_ollama()
            await self._check_tradingagents()

        asyncio.create_task(check())

    async def _check_ollama(self) -> None:
        """Check if Ollama is running."""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    self.settings.ollama_base_url.replace("/v1", "/api/tags")
                )
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [m.get("name", "") for m in models]
                    if self.settings.ollama_quick_model in model_names:
                        self.ollama_status = "connected"
                    else:
                        self.ollama_status = f"connected (model not found: {self.settings.ollama_quick_model})"
                else:
                    self.ollama_status = f"error {response.status_code}"
        except Exception as e:
            self.ollama_status = f"unreachable ({type(e).__name__})"
            logger.warning("ollama_check_failed", error=str(e))

    async def _check_tradingagents(self) -> None:
        """Check if TradingAgents is installed."""
        try:
            import importlib.util

            spec = importlib.util.find_spec("tradingagents")
            if spec is not None:
                self.tradingagents_status = "available"
            else:
                self.tradingagents_status = "not installed"
        except Exception as e:
            self.tradingagents_status = f"error ({type(e).__name__})"
            logger.warning("tradingagents_check_failed", error=str(e))

    def action_help(self) -> None:
        """Show help modal."""
        self.push_screen(HelpModal())

    def action_schema_help(self) -> None:
        """Show schema help modal."""
        self.push_screen(SchemaHelpModal())

    async def action_quit(self) -> None:
        """Quit the application."""
        logger.info("bloomfolio_app_quitting")
        self.exit()

    def action_escape(self) -> None:
        """Close modal or cancel."""
        if len(self.screen_stack) > 1:
            self.pop_screen()

    def action_command_palette(self) -> None:
        """Open command palette."""
        super().action_command_palette()

    def action_import_csv(self) -> None:
        """Import portfolio CSV."""
        self.log_ui("Opening import screen...")
        from bloomfolio.tui.screens.import_portfolio import ImportPortfolioScreen

        self.push_screen(ImportPortfolioScreen())

    def action_portfolio(self) -> None:
        """Show portfolio overview."""
        self.log_ui("Opening portfolio overview...")
        from bloomfolio.tui.screens.portfolio_overview import PortfolioOverviewScreen

        self.push_screen(PortfolioOverviewScreen())

    def action_run_analysis(self) -> None:
        """Run analysis."""
        if self.current_portfolio is None:
            self.log_ui("[yellow]No portfolio imported. Press 'i' to import.[/yellow]")
            self.notify("No portfolio imported. Press 'i' to import.", severity="warning")
            return
        self.log_ui("Opening agent monitor...")
        from bloomfolio.tui.screens.agent_monitor import AgentMonitorScreen

        self.push_screen(AgentMonitorScreen(self.current_portfolio))

    def action_agent_monitor(self) -> None:
        """Open agent monitor (same as run analysis for now)."""
        self.action_run_analysis()

    def action_validate_csv(self) -> None:
        """Validate current portfolio source file or open import screen."""
        portfolio = self.current_portfolio
        if portfolio is not None and portfolio.source_file_name:
            self.log_ui(f"Validating {portfolio.source_file_name}...")
            import asyncio

            from bloomfolio.portfolio.validator import validate_csv_file

            async def _validate(path: str) -> None:
                try:
                    result = await validate_csv_file(path)
                    if result.valid:
                        self.log_ui(
                            f"[green]Valid: {result.row_count} rows[/green]"
                        )
                        self.notify(
                            f"Valid: {result.row_count} rows",
                            severity="information",
                        )
                    else:
                        self.log_ui(
                            f"[red]Invalid: {len(result.errors)} errors[/red]"
                        )
                        self.notify(
                            f"Invalid: {len(result.errors)} errors",
                            severity="error",
                        )
                except Exception as e:
                    self.log_ui(f"[red]Validation failed: {e}[/red]")
                    self.notify(f"Validation failed: {e}", severity="error")

            asyncio.create_task(_validate(portfolio.source_file_name))
        else:
            self.log_ui("No portfolio loaded — opening import screen")
            from bloomfolio.tui.screens.import_portfolio import ImportPortfolioScreen

            self.push_screen(ImportPortfolioScreen())

    def action_export(self) -> None:
        """Export report."""
        if self.current_portfolio is None:
            self.log_ui("[yellow]No portfolio to export. Press 'i' to import.[/yellow]")
            self.notify("No portfolio to export. Press 'i' to import.", severity="warning")
            return
        self.log_ui("Opening export screen...")
        from bloomfolio.tui.screens.export import ExportScreen

        self.push_screen(ExportScreen(self.current_portfolio))

    def action_cancel_task(self) -> None:
        """Cancel active task."""
        self.notify("Cancel requested", severity="information")

    def action_clear_logs(self) -> None:
        """Clear log panel."""
        try:
            from bloomfolio.tui.widgets.log_panel import CommandLog

            log = self.query_one("#command-log", CommandLog)
            log.clear()
        except Exception:
            pass
        self.notify("Logs cleared", severity="information")

    def log_ui(self, message: str) -> None:
        """Write a message to the bottom command log on the current screen."""
        try:
            from bloomfolio.tui.widgets.log_panel import CommandLog

            log = self.query_one(CommandLog)
            log.write_line(message)
        except Exception:
            pass

    def watch_current_portfolio(self, portfolio: Portfolio | None) -> None:
        """React to portfolio changes."""
        if portfolio is not None:
            self.notify(
                f"Portfolio imported: {len(portfolio.holdings)} holdings",
                severity="information",
            )
