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
from bloomfolio.tui.screens.dashboard import DashboardScreen
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
    analysis_results: reactive[dict[str, Any]] = reactive({})
    provider_status: reactive[str] = reactive("checking...")
    tradingagents_status: reactive[str] = reactive("checking...")

    def __init__(self) -> None:
        super().__init__()
        self.settings = get_settings()
        configure_logging()
        logger.info("bloomfolio_app_initializing")

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.register_theme(BLOOMFOLIO_THEME)
        self.theme = "bloomfolio"
        self.push_screen(DashboardScreen())
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Check LLM provider and TradingAgents status asynchronously."""
        import asyncio

        async def check() -> None:
            await self._check_provider()
            await self._check_tradingagents()

        asyncio.create_task(check())

    async def _check_provider(self) -> None:
        """Check configured LLM provider availability."""
        provider = self.settings.llm_provider
        try:
            if provider == "ollama":
                import httpx

                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(
                        self.settings.ollama_base_url.replace("/v1", "/api/tags")
                    )
                    if response.status_code == 200:
                        models = response.json().get("models", [])
                        model_names = [m.get("name", "") for m in models]
                        if self.settings.ollama_quick_model in model_names:
                            self.provider_status = "ollama: connected"
                        else:
                            self.provider_status = (
                                f"ollama: model missing ({self.settings.ollama_quick_model})"
                            )
                    else:
                        self.provider_status = f"ollama: error {response.status_code}"
            elif provider == "openrouter":
                import httpx

                api_key = self.settings.openrouter_api_key
                if not api_key:
                    self.provider_status = "openrouter: no api key"
                    return
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        "https://openrouter.ai/api/v1/models",
                        headers={"Authorization": f"Bearer {api_key}"},
                    )
                    if response.status_code == 200:
                        data = response.json()
                        model_ids = [m.get("id", "") for m in data.get("data", [])]
                        if self.settings.openrouter_model in model_ids:
                            self.provider_status = f"openrouter: {self.settings.openrouter_model}"
                        else:
                            self.provider_status = (
                                f"openrouter: connected ({self.settings.openrouter_model} not listed)"
                            )
                    else:
                        self.provider_status = f"openrouter: error {response.status_code}"
            else:
                self.provider_status = f"{provider}: unknown provider"
        except Exception as e:
            self.provider_status = f"{provider}: unreachable ({type(e).__name__})"
            logger.warning("provider_check_failed", provider=provider, error=str(e))

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

    def watch_current_portfolio(self, portfolio: Portfolio | None) -> None:
        """React to portfolio changes."""
        if portfolio is not None:
            self.notify(
                f"Portfolio imported: {len(portfolio.holdings)} holdings",
                severity="information",
            )
            # Propagate to dashboard (it may be under a modal in the stack)
            for screen in self.screen_stack:
                if isinstance(screen, DashboardScreen):
                    screen.watch_current_portfolio()

    def watch_analysis_results(self, results: dict[str, Any]) -> None:
        """React to analysis completion."""
        for screen in self.screen_stack:
            if isinstance(screen, DashboardScreen):
                screen.watch_analysis_results()
