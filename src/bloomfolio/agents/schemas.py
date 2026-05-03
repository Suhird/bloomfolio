"""Agent output schemas for structured LLM responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FundamentalAnalysis(BaseModel):
    """Fundamental analyst output."""

    ticker: str
    summary: str = ""
    key_metrics: dict[str, str] = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    valuation_assessment: str = ""


class TechnicalAnalysis(BaseModel):
    """Technical analyst output."""

    ticker: str
    summary: str = ""
    trend: str = ""
    support_levels: list[str] = Field(default_factory=list)
    resistance_levels: list[str] = Field(default_factory=list)
    indicators: dict[str, str] = Field(default_factory=dict)


class NewsAnalysis(BaseModel):
    """News analyst output."""

    ticker: str
    summary: str = ""
    key_headlines: list[str] = Field(default_factory=list)
    sentiment: str = "neutral"
    catalysts: list[str] = Field(default_factory=list)


class SentimentAnalysis(BaseModel):
    """Sentiment analyst output."""

    ticker: str
    summary: str = ""
    overall_sentiment: str = "neutral"
    social_sentiment: str = "neutral"
    news_sentiment: str = "neutral"
    sentiment_score: float = Field(default=0.0, ge=-1, le=1)


class BullCase(BaseModel):
    """Bull researcher output."""

    ticker: str
    thesis: str = ""
    key_arguments: list[str] = Field(default_factory=list)
    upside_scenarios: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)


class BearCase(BaseModel):
    """Bear researcher output."""

    ticker: str
    thesis: str = ""
    key_arguments: list[str] = Field(default_factory=list)
    downside_scenarios: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)


class TraderSynthesis(BaseModel):
    """Trader synthesis output."""

    ticker: str
    summary: str = ""
    rating: str = "neutral"
    action_label: str = "no_action"
    time_horizon: str = "medium"
    key_factors: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)


class RiskReview(BaseModel):
    """Risk review output."""

    ticker: str
    summary: str = ""
    risk_factors: list[str] = Field(default_factory=list)
    risk_level: str = "medium"
    mitigation_notes: list[str] = Field(default_factory=list)


class PortfolioManagerConclusion(BaseModel):
    """Portfolio manager conclusion."""

    ticker: str
    final_rating: str = "neutral"
    final_action_label: str = "no_action"
    thesis: str = ""
    bull_case: str = ""
    bear_case: str = ""
    risk_notes: list[str] = Field(default_factory=list)
    portfolio_context_notes: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    key_uncertainties: list[str] = Field(default_factory=list)
