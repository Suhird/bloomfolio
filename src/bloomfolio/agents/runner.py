"""Analysis runner orchestrating multi-agent workflow."""

from __future__ import annotations

import asyncio
from typing import Any

from bloomfolio.agents.fallback_graph import FallbackAnalysisGraph
from bloomfolio.agents.tradingagents_gateway import TradingAgentsGateway
from bloomfolio.config.settings import get_settings
from bloomfolio.domain.enums import AuditEventType
from bloomfolio.domain.portfolio import Portfolio
from bloomfolio.domain.reports import TickerAnalysisResult
from bloomfolio.observability.logging import get_logger
from bloomfolio.storage.audit import log_audit_event

logger = get_logger(__name__)


class AnalysisRunner:
    """Orchestrates portfolio-wide multi-agent analysis."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.ta_gateway = TradingAgentsGateway()
        self.fallback_graph = FallbackAnalysisGraph()
        self.semaphore = asyncio.Semaphore(self.settings.max_concurrent_tickers)
        self._cancelled = False

    async def run_portfolio_analysis(
        self,
        portfolio: Portfolio,
        progress_callback: Any | None = None,
    ) -> dict[str, TickerAnalysisResult]:
        """Run analysis for all tickers in portfolio.

        Args:
            portfolio: Portfolio to analyze.
            progress_callback: Optional callback(ticker, stage) for progress updates.

        Returns:
            Dict mapping ticker to analysis result.
        """
        tickers = portfolio.get_tickers()
        if not tickers:
            return {}

        await log_audit_event(
            event_type=AuditEventType.START_ANALYSIS,
            metadata={"tickers": tickers, "portfolio_id": str(portfolio.id)},
        )

        self._cancelled = False
        results: dict[str, TickerAnalysisResult] = {}

        async def analyze_one(ticker: str) -> tuple[str, TickerAnalysisResult]:
            async with self.semaphore:
                if self._cancelled:
                    return ticker, TickerAnalysisResult(
                        ticker=ticker, errors=["Cancelled"]
                    )
                try:
                    result = await self._analyze_ticker(ticker, portfolio, progress_callback)
                    return ticker, result
                except Exception as e:
                    logger.error("ticker_analysis_failed", ticker=ticker, error=str(e))
                    return ticker, TickerAnalysisResult(ticker=ticker, errors=[str(e)])

        tasks = [asyncio.create_task(analyze_one(t)) for t in tickers]
        for task in asyncio.as_completed(tasks):
            ticker, result = await task
            results[ticker] = result
            if progress_callback:
                await progress_callback(ticker, "complete")

        await log_audit_event(
            event_type=AuditEventType.COMPLETE_ANALYSIS,
            metadata={
                "tickers": tickers,
                "portfolio_id": str(portfolio.id),
                "results_count": len(results),
            },
        )

        return results

    async def _analyze_ticker(
        self,
        ticker: str,
        portfolio: Portfolio,
        progress_callback: Any | None = None,
    ) -> TickerAnalysisResult:
        """Analyze a single ticker."""
        holding = next(
            (h for h in portfolio.holdings if h.ticker == ticker),
            None,
        )

        # Try TradingAgents first if available
        if self.ta_gateway.is_available():
            try:
                return await self.ta_gateway.analyze_ticker(
                    ticker, holding, portfolio, progress_callback
                )
            except Exception as e:
                logger.warning(
                    "tradingagents_fallback",
                    ticker=ticker,
                    error=str(e),
                )

        # Use fallback graph
        market_data: dict[str, Any] = {}
        news_items: list[dict[str, Any]] = []
        sentiment_data: dict[str, Any] = {}

        return await self.fallback_graph.analyze_ticker(
            ticker=ticker,
            holding=holding,
            portfolio=portfolio,
            market_data=market_data,
            news_items=news_items,
            sentiment_data=sentiment_data,
            progress_callback=progress_callback,
        )

    def cancel(self) -> None:
        """Signal cancellation."""
        self._cancelled = True
        logger.info("analysis_cancel_requested")
