"""TradingAgents gateway and adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bloomfolio.config.settings import get_settings
from bloomfolio.domain.exceptions import TradingAgentsIntegrationError
from bloomfolio.domain.reports import TickerAnalysisResult
from bloomfolio.observability.logging import get_logger

if TYPE_CHECKING:
    from bloomfolio.domain.portfolio import Holding, Portfolio

logger = get_logger(__name__)


class TradingAgentsGateway:
    """Gateway to upstream TradingAgents library."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._available = False
        self._graph_class: Any = None
        self._config_class: Any = None
        self._try_import()

    def _try_import(self) -> None:
        """Try to import TradingAgents."""
        try:
            import importlib

            tradingagents_graph = importlib.import_module("tradingagents.graph.trading_graph")
            tradingagents_config = importlib.import_module("tradingagents.default_config")

            self._graph_class = tradingagents_graph.TradingAgentsGraph
            self._config_class = tradingagents_config.DEFAULT_CONFIG
            self._available = True
            logger.info("tradingagents_import_success")
        except ImportError:
            self._available = False
            logger.info("tradingagents_not_available")

    def is_available(self) -> bool:
        """Check if TradingAgents is available."""
        return self._available and self.settings.enable_tradingagents

    async def analyze_ticker(
        self,
        ticker: str,
        holding: Holding | None = None,
        portfolio: Portfolio | None = None,
        progress_callback: Any | None = None,
    ) -> TickerAnalysisResult:
        """Run TradingAgents analysis on a ticker.

        Args:
            ticker: Ticker symbol.
            holding: User's holding info.
            portfolio: Full portfolio context.
            progress_callback: Optional progress callback.

        Returns:
            TickerAnalysisResult.

        Raises:
            TradingAgentsIntegrationError: If analysis fails.
        """
        if not self.is_available():
            raise TradingAgentsIntegrationError("TradingAgents not available")

        import asyncio

        config = self._config_class.copy()
        config["llm_provider"] = self.settings.llm_provider
        config["quick_think_llm"] = self.settings.ollama_quick_model
        config["deep_think_llm"] = self.settings.ollama_deep_model
        config["max_debate_rounds"] = self.settings.max_debate_rounds

        try:
            # TradingAgents propagate is synchronous, run in thread
            loop = asyncio.get_event_loop()
            graph = self._graph_class(debug=False, config=config)

            def _run() -> Any:
                return graph.propagate(ticker)

            _, decision = await loop.run_in_executor(None, _run)

            # Convert TradingAgents decision to our format
            result = TickerAnalysisResult(ticker=ticker)
            from bloomfolio.domain.enums import ActionLabel, Rating

            result.decision = TradingDecision(
                ticker=ticker,
                rating=Rating(getattr(decision, "rating", "neutral")),
                action_label=ActionLabel.RESEARCH_MORE,
                thesis=getattr(decision, "thesis", ""),
                confidence=0.7,
            )
            return result
        except Exception as e:
            logger.error("tradingagents_analysis_failed", ticker=ticker, error=str(e))
            raise TradingAgentsIntegrationError(f"TradingAgents analysis failed: {e}") from e


from bloomfolio.domain.reports import TradingDecision  # noqa: E402
