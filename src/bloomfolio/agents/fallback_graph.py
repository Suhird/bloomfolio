"""Fallback multi-agent analysis graph.

Implements a TradingAgents-compatible workflow when the upstream
package is not available.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from bloomfolio.agents.prompts import (
    build_bear_prompt,
    build_bull_prompt,
    build_fundamental_prompt,
    build_news_prompt,
    build_portfolio_manager_prompt,
    build_risk_prompt,
    build_sentiment_prompt,
    build_technical_prompt,
    build_trader_prompt,
)
from bloomfolio.agents.schemas import (
    BearCase,
    BullCase,
    FundamentalAnalysis,
    NewsAnalysis,
    PortfolioManagerConclusion,
    RiskReview,
    SentimentAnalysis,
    TechnicalAnalysis,
    TraderSynthesis,
)
from bloomfolio.domain.enums import AnalysisStage
from bloomfolio.domain.portfolio import Holding, Portfolio
from bloomfolio.domain.reports import AnalystReport, TickerAnalysisResult, TradingDecision
from bloomfolio.llm.client import ChatMessage, LLMGateway
from bloomfolio.observability.logging import get_logger

logger = get_logger(__name__)


def _safe_list(obj: Any, fallback: list[str] | None = None) -> list[str]:
    """Ensure obj is a list of strings."""
    if fallback is None:
        fallback = []
    if isinstance(obj, list):
        return [str(item) for item in obj]
    if isinstance(obj, str):
        return [obj]
    return fallback


def _safe_str(obj: Any, fallback: str = "") -> str:
    """Ensure obj is a string."""
    if isinstance(obj, str):
        return obj
    if obj is None:
        return fallback
    return str(obj)


def _safe_float(obj: Any, fallback: float = 0.5) -> float:
    """Ensure obj is a float."""
    try:
        return float(obj)
    except Exception:
        return fallback


class FallbackAnalysisGraph:
    """Internal fallback analysis graph compatible with TradingAgents workflow."""

    def __init__(self, llm_gateway: LLMGateway | None = None) -> None:
        self.llm = llm_gateway or LLMGateway()

    async def analyze_ticker(
        self,
        ticker: str,
        holding: Holding | None,
        portfolio: Portfolio | None,
        market_data: dict[str, Any],
        news_items: list[dict[str, Any]],
        sentiment_data: dict[str, Any],
        progress_callback: Any | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> TickerAnalysisResult:
        """Run full multi-agent analysis on a ticker.

        Args:
            ticker: Ticker symbol.
            holding: User's holding info.
            portfolio: Full portfolio context.
            market_data: Market data dict.
            news_items: News items list.
            sentiment_data: Sentiment data dict.
            progress_callback: Optional progress callback.

        Returns:
            TickerAnalysisResult with all reports and decision.
        """
        result = TickerAnalysisResult(ticker=ticker)
        analyses: dict[str, Any] = {}

        stages = [
            ("fundamental", AnalysisStage.FUNDAMENTAL),
            ("technical", AnalysisStage.TECHNICAL),
            ("news", AnalysisStage.NEWS),
            ("sentiment", AnalysisStage.SENTIMENT),
            ("bull", AnalysisStage.BULL_RESEARCH),
            ("bear", AnalysisStage.BEAR_RESEARCH),
            ("trader", AnalysisStage.TRADER_SYNTHESIS),
            ("risk", AnalysisStage.RISK_REVIEW),
            ("portfolio_manager", AnalysisStage.PORTFOLIO_MANAGER),
        ]

        for stage_name, _stage in stages:
            if should_cancel and should_cancel():
                result.errors.append("Cancelled by user")
                break

            if progress_callback:
                await progress_callback(ticker, stage_name)

            try:
                report = await self._run_stage(
                    stage_name, ticker, holding, portfolio, analyses,
                    market_data, news_items, sentiment_data,
                )
                if report:
                    result.reports.append(report)
                    analyses[stage_name] = report
            except Exception as e:
                logger.warning("fallback_stage_failed", ticker=ticker, stage=stage_name, error=str(e))
                result.errors.append(f"{stage_name}: {e}")

        # Build final decision from portfolio manager report
        pm_report = analyses.get("portfolio_manager")
        if pm_report and isinstance(pm_report, dict):
            result.decision = TradingDecision(
                ticker=ticker,
                rating=pm_report.get("final_rating", "neutral"),
                action_label=pm_report.get("final_action_label", "no_action"),
                thesis=pm_report.get("thesis", ""),
                bull_case=pm_report.get("bull_case", ""),
                bear_case=pm_report.get("bear_case", ""),
                risk_notes=pm_report.get("risk_notes", []),
                portfolio_context_notes=pm_report.get("portfolio_context_notes", []),
                confidence=pm_report.get("confidence", 0.5),
                key_uncertainties=pm_report.get("key_uncertainties", []),
            )

        return result

    async def _run_stage(
        self,
        stage: str,
        ticker: str,
        holding: Holding | None,
        portfolio: Portfolio | None,
        analyses: dict[str, Any],
        market_data: dict[str, Any],
        news_items: list[dict[str, Any]],
        sentiment_data: dict[str, Any],
    ) -> AnalystReport | None:
        """Run a single analysis stage."""
        if stage == "fundamental":
            prompt = build_fundamental_prompt(ticker, holding, market_data)
            output: Any = await self.llm.complete_json(
                [ChatMessage(role="user", content=prompt)],
                FundamentalAnalysis,
                temperature=0.3,
            )
            return AnalystReport(
                ticker=ticker,
                agent_name="Fundamental Analyst",
                stage=AnalysisStage.FUNDAMENTAL,
                summary=_safe_str(getattr(output, "summary", "")),
                key_points=_safe_list(getattr(output, "strengths", [])) + _safe_list(getattr(output, "weaknesses", [])),
                confidence=0.7,
            )

        elif stage == "technical":
            prompt = build_technical_prompt(ticker, market_data)
            output = await self.llm.complete_json(
                [ChatMessage(role="user", content=prompt)],
                TechnicalAnalysis,
                temperature=0.3,
            )
            return AnalystReport(
                ticker=ticker,
                agent_name="Technical Analyst",
                stage=AnalysisStage.TECHNICAL,
                summary=_safe_str(getattr(output, "summary", "")),
                key_points=[_safe_str(getattr(output, "trend", ""))] + _safe_list(getattr(output, "support_levels", [])) + _safe_list(getattr(output, "resistance_levels", [])),
                confidence=0.6,
            )

        elif stage == "news":
            prompt = build_news_prompt(ticker, news_items)
            output = await self.llm.complete_json(
                [ChatMessage(role="user", content=prompt)],
                NewsAnalysis,
                temperature=0.3,
            )
            return AnalystReport(
                ticker=ticker,
                agent_name="News Analyst",
                stage=AnalysisStage.NEWS,
                summary=_safe_str(getattr(output, "summary", "")),
                key_points=_safe_list(getattr(output, "key_headlines", [])) + _safe_list(getattr(output, "catalysts", [])),
                confidence=0.5,
            )

        elif stage == "sentiment":
            prompt = build_sentiment_prompt(ticker, sentiment_data)
            output = await self.llm.complete_json(
                [ChatMessage(role="user", content=prompt)],
                SentimentAnalysis,
                temperature=0.3,
            )
            return AnalystReport(
                ticker=ticker,
                agent_name="Sentiment Analyst",
                stage=AnalysisStage.SENTIMENT,
                summary=_safe_str(getattr(output, "summary", "")),
                key_points=[
                    f"Overall: {_safe_str(getattr(output, 'overall_sentiment', 'neutral'))}",
                    f"Score: {_safe_float(getattr(output, 'sentiment_score', 0.0)):.2f}",
                ],
                confidence=0.5,
            )

        elif stage == "bull":
            prompt = build_bull_prompt(ticker, analyses)
            output = await self.llm.complete_json(
                [ChatMessage(role="user", content=prompt)],
                BullCase,
                temperature=0.5,
            )
            return AnalystReport(
                ticker=ticker,
                agent_name="Bull Researcher",
                stage=AnalysisStage.BULL_RESEARCH,
                summary=_safe_str(getattr(output, "thesis", "")),
                key_points=_safe_list(getattr(output, "key_arguments", [])) + _safe_list(getattr(output, "upside_scenarios", [])),
                confidence=_safe_float(getattr(output, "confidence", 0.5)),
            )

        elif stage == "bear":
            prompt = build_bear_prompt(ticker, analyses)
            output = await self.llm.complete_json(
                [ChatMessage(role="user", content=prompt)],
                BearCase,
                temperature=0.5,
            )
            return AnalystReport(
                ticker=ticker,
                agent_name="Bear Researcher",
                stage=AnalysisStage.BEAR_RESEARCH,
                summary=_safe_str(getattr(output, "thesis", "")),
                key_points=_safe_list(getattr(output, "key_arguments", [])) + _safe_list(getattr(output, "downside_scenarios", [])),
                confidence=_safe_float(getattr(output, "confidence", 0.5)),
            )

        elif stage == "trader":
            bull = analyses.get("bull", {})
            bear = analyses.get("bear", {})
            prompt = build_trader_prompt(ticker, bull, bear, analyses)
            output = await self.llm.complete_json(
                [ChatMessage(role="user", content=prompt)],
                TraderSynthesis,
                temperature=0.4,
            )
            return AnalystReport(
                ticker=ticker,
                agent_name="Trader",
                stage=AnalysisStage.TRADER_SYNTHESIS,
                summary=_safe_str(getattr(output, "summary", "")),
                key_points=_safe_list(getattr(output, "key_factors", [])),
                confidence=_safe_float(getattr(output, "confidence", 0.5)),
            )

        elif stage == "risk":
            prompt = build_risk_prompt(ticker, holding, analyses)
            output = await self.llm.complete_json(
                [ChatMessage(role="user", content=prompt)],
                RiskReview,
                temperature=0.3,
            )
            return AnalystReport(
                ticker=ticker,
                agent_name="Risk Manager",
                stage=AnalysisStage.RISK_REVIEW,
                summary=_safe_str(getattr(output, "summary", "")),
                key_points=_safe_list(getattr(output, "risk_factors", [])) + _safe_list(getattr(output, "mitigation_notes", [])),
                confidence=0.6,
            )

        elif stage == "portfolio_manager":
            trader = analyses.get("trader", {})
            risk = analyses.get("risk", {})
            prompt = build_portfolio_manager_prompt(ticker, holding, portfolio, trader, risk)
            output = await self.llm.complete_json(
                [ChatMessage(role="user", content=prompt)],
                PortfolioManagerConclusion,
                temperature=0.3,
            )
            # Store the raw dict for decision building
            raw_dict: dict[str, Any] = {}
            if hasattr(output, "model_dump"):
                raw_dict = output.model_dump()
            elif isinstance(output, dict):
                raw_dict = output
            analyses["portfolio_manager"] = raw_dict
            return AnalystReport(
                ticker=ticker,
                agent_name="Portfolio Manager",
                stage=AnalysisStage.PORTFOLIO_MANAGER,
                summary=_safe_str(getattr(output, "thesis", "")),
                key_points=_safe_list(getattr(output, "risk_notes", [])) + _safe_list(getattr(output, "portfolio_context_notes", [])),
                confidence=_safe_float(getattr(output, "confidence", 0.5)),
            )

        return None
