"""Configuration settings using pydantic-settings."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="BLOOMFOLIO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "dev"
    log_level: str = "INFO"

    base_currency: str = "CAD"

    # LLM Provider
    llm_provider: str = "ollama"

    # Ollama settings
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_api_key: str = "ollama"
    ollama_quick_model: str = "gemma4:latest"
    ollama_deep_model: str = "gemma4:latest"

    # OpenRouter settings
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str = ""
    openrouter_model: str = "MiniMax/MiniMax-M2-7B"

    # Analysis settings
    max_debate_rounds: int = 2
    max_concurrent_tickers: int = 2
    max_concurrent_llm_requests: int = 1
    analysis_timeout_seconds: int = 900

    # Feature flags
    enable_tradingagents: bool = True
    enable_fallback_graph: bool = True
    enable_network_marketdata: bool = True
    enable_experimental_action_labels: bool = False

    # Data directory
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".local" / "share" / "bloomfolio")

    @field_validator("data_dir", mode="before")
    @classmethod
    def _resolve_data_dir(cls, v: str | Path | None) -> Path:
        if v is None:
            return Path.home() / ".local" / "share" / "bloomfolio"
        return Path(v)

    @property
    def db_path(self) -> Path:
        """Path to SQLite database."""
        return self.data_dir / "bloomfolio.sqlite3"

    @property
    def cache_dir(self) -> Path:
        """Path to cache directory."""
        return self.data_dir / "cache"

    def get_llm_config(self) -> dict[str, str | int]:
        """Get LLM configuration for current provider."""
        if self.llm_provider == "ollama":
            return {
                "provider": "ollama",
                "base_url": self.ollama_base_url,
                "api_key": self.ollama_api_key,
                "quick_model": self.ollama_quick_model,
                "deep_model": self.ollama_deep_model,
            }
        if self.llm_provider == "openrouter":
            return {
                "provider": "openrouter",
                "base_url": self.openrouter_base_url,
                "api_key": self.openrouter_api_key,
                "model": self.openrouter_model,
            }
        return {
            "provider": self.llm_provider,
            "base_url": self.ollama_base_url,
            "api_key": self.ollama_api_key,
            "quick_model": self.ollama_quick_model,
            "deep_model": self.ollama_deep_model,
        }


_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create cached settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Force reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings
