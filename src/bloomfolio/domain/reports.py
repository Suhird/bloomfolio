"""Report and analysis domain models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from bloomfolio.domain.enums import ActionLabel, AnalysisStage, Rating, TimeHorizon


def _utc_now() -> datetime:
    return datetime.now(UTC)


class EvidenceItem(BaseModel):
    """Evidence item for analyst reports."""

    source: str
    content: str
    confidence: float = Field(ge=0, le=1)


class AnalystReport(BaseModel):
    """Single analyst agent report."""

    ticker: str
    agent_name: str
    stage: AnalysisStage
    summary: str = ""
    key_points: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    generated_at: datetime = Field(default_factory=_utc_now)


class TradingDecision(BaseModel):
    """Final trading decision."""

    ticker: str
    rating: Rating = Rating.NEUTRAL
    action_label: ActionLabel = ActionLabel.NO_ACTION
    time_horizon: TimeHorizon = TimeHorizon.MEDIUM
    thesis: str = ""
    bull_case: str = ""
    bear_case: str = ""
    risk_notes: list[str] = Field(default_factory=list)
    portfolio_context_notes: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    key_uncertainties: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "This analysis is for research purposes only and does not constitute financial advice."
    )
    generated_at: datetime = Field(default_factory=_utc_now)


class TickerAnalysisResult(BaseModel):
    """Complete ticker analysis result."""

    ticker: str
    resolved_ticker: str | None = None
    portfolio_context: dict[str, Any] = Field(default_factory=dict)
    market_data_freshness: datetime | None = None
    reports: list[AnalystReport] = Field(default_factory=list)
    decision: TradingDecision | None = None
    errors: list[str] = Field(default_factory=list)
    completed_at: datetime | None = None


class TaskResult[T](BaseModel):
    """Generic task result with partial failure support."""

    ok: bool
    value: T | None = None
    error: str | None = None

    @classmethod
    def success(cls, value: T) -> TaskResult[T]:
        return cls(ok=True, value=value)

    @classmethod
    def failure(cls, error: str) -> TaskResult[T]:
        return cls(ok=False, error=error)
