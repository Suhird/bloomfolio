"""Domain enums."""

from enum import StrEnum


class AssetType(StrEnum):
    """Asset type enumeration."""

    STOCK = "stock"
    ETF = "etf"
    CASH = "cash"
    CRYPTO = "crypto"
    BOND = "bond"
    OTHER = "other"
    UNKNOWN = "unknown"


class AnalysisStage(StrEnum):
    """Analysis stage enumeration."""

    MARKET_DATA = "market_data"
    FUNDAMENTAL = "fundamental"
    TECHNICAL = "technical"
    NEWS = "news"
    SENTIMENT = "sentiment"
    BULL_RESEARCH = "bull_research"
    BEAR_RESEARCH = "bear_research"
    TRADER_SYNTHESIS = "trader_synthesis"
    RISK_REVIEW = "risk_review"
    PORTFOLIO_MANAGER = "portfolio_manager"
    COMPLETE = "complete"


class Rating(StrEnum):
    """Research rating enumeration."""

    STRONG_BEARISH = "strong_bearish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    BULLISH = "bullish"
    STRONG_BULLISH = "strong_bullish"


class ActionLabel(StrEnum):
    """Non-advisory action label enumeration."""

    WATCH = "watch"
    RESEARCH_MORE = "research_more"
    REBALANCE_CANDIDATE = "rebalance_candidate"
    RISK_REVIEW = "risk_review"
    NO_ACTION = "no_action"


class TimeHorizon(StrEnum):
    """Time horizon enumeration."""

    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class AuditEventType(StrEnum):
    """Audit event type enumeration."""

    IMPORT_PORTFOLIO = "import_portfolio"
    VALIDATE_PORTFOLIO = "validate_portfolio"
    START_ANALYSIS = "start_analysis"
    CANCEL_ANALYSIS = "cancel_analysis"
    COMPLETE_ANALYSIS = "complete_analysis"
    FAILED_ANALYSIS = "failed_analysis"
    EXPORT_REPORT = "export_report"
    SETTINGS_CHANGE = "settings_change"
    CACHE_CLEAR = "cache_clear"
