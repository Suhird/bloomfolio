"""Domain exceptions."""


class BloomFolioError(Exception):
    """Base exception for all BloomFolio errors."""


class PortfolioValidationError(BloomFolioError):
    """Raised when portfolio CSV validation fails."""


class LLMOutputValidationError(BloomFolioError):
    """Raised when LLM output fails schema validation."""


class MarketDataProviderError(BloomFolioError):
    """Raised when market data provider fails."""


class TradingAgentsIntegrationError(BloomFolioError):
    """Raised when TradingAgents integration fails."""


class StorageError(BloomFolioError):
    """Raised when storage operation fails."""


class GatewayError(BloomFolioError):
    """Raised when gateway operation fails."""
