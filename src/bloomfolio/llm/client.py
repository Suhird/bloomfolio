"""LLM gateway for structured output."""

from __future__ import annotations

import hashlib
import json

import httpx
from pydantic import BaseModel, ValidationError

from bloomfolio.config.settings import Settings, get_settings
from bloomfolio.domain.exceptions import LLMOutputValidationError
from bloomfolio.domain.reports import TaskResult
from bloomfolio.observability.logging import get_logger
from bloomfolio.storage.audit import log_audit_event
from bloomfolio.storage.cache import get_cached, set_cached

logger = get_logger(__name__)


class ChatMessage(BaseModel):
    """Chat message for LLM completion."""

    role: str
    content: str


class LLMGateway:
    """Gateway for LLM completions with structured output validation."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.provider = self.settings.llm_provider
        self.config = self.settings.get_llm_config()

    async def complete_json[
        T: BaseModel
    ](
        self,
        messages: list[ChatMessage],
        schema: type[T],
        temperature: float = 0.7,
        timeout_seconds: int = 300,
        model_override: str | None = None,
    ) -> T:
        """Complete and validate structured JSON output.

        Args:
            messages: Chat messages.
            schema: Pydantic model for validation.
            temperature: Sampling temperature.
            timeout_seconds: Request timeout.
            model_override: Optional model override.

        Returns:
            Validated Pydantic model instance.

        Raises:
            LLMOutputValidationError: If validation fails after retry.
        """
        prompt_text = json.dumps([m.model_dump() for m in messages])
        prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()[:16]
        model_name = model_override or self._get_model_name()
        cache_key = f"llm|{model_name}|{prompt_hash}|{schema.__name__}"

        # Check cache
        cached = await get_cached(cache_key)
        if cached:
            logger.info("llm_cache_hit", model=model_name, prompt_hash=prompt_hash)
            try:
                return schema.model_validate(cached)
            except ValidationError:
                pass

        raw = await self._call_llm(messages, model_name, temperature, timeout_seconds)

        # First parse attempt
        result = self._parse_and_validate(raw, schema, prompt_hash, model_name)
        if result.ok and result.value is not None:
            await set_cached(cache_key, result.value.model_dump())
            return result.value

        # One repair attempt
        logger.warning("llm_parse_failed_attempting_repair", error=result.error)
        repair_messages = messages + [
            ChatMessage(
                role="user",
                content=(
                    "Your previous response failed validation. "
                    "Please output ONLY valid JSON matching the required schema. "
                    f"Error: {result.error}"
                ),
            )
        ]
        raw_repair = await self._call_llm(repair_messages, model_name, temperature, timeout_seconds)
        result_repair = self._parse_and_validate(raw_repair, schema, prompt_hash, model_name)

        if result_repair.ok and result_repair.value is not None:
            await set_cached(cache_key, result_repair.value.model_dump())
            return result_repair.value

        # Log failure
        await log_audit_event(
            event_type="failed_analysis",  # type: ignore[arg-type]
            metadata={
                "model": model_name,
                "prompt_hash": prompt_hash,
                "error": result_repair.error,
                "raw_output_preview": raw[:500],
            },
        )
        raise LLMOutputValidationError(
            f"LLM output validation failed after retry: {result_repair.error}"
        )

    def _get_model_name(self) -> str:
        """Get model name for current provider."""
        if self.provider == "openrouter":
            return str(self.config.get("model", "MiniMax/MiniMax-M2-7B"))
        return str(self.config.get("deep_model", "gemma4:26b"))

    async def _call_llm(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float,
        timeout: int,
    ) -> str:
        """Call LLM API."""
        base_url = str(self.config.get("base_url", "http://localhost:11434/v1"))
        api_key = str(self.config.get("api_key", ""))

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/bloomfolio"
            headers["X-Title"] = "BloomFolio"

        payload = {
            "model": model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content: str = data["choices"][0]["message"]["content"]

            # Strip markdown code blocks if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            return content.strip()

    def _parse_and_validate[
        T: BaseModel
    ](
        self,
        raw: str,
        schema: type[T],
        prompt_hash: str,
        model_name: str,
    ) -> TaskResult[T]:
        """Parse raw JSON and validate against schema."""
        try:
            data = json.loads(raw)
            instance = schema.model_validate(data)
            logger.info(
                "llm_output_validated",
                model=model_name,
                prompt_hash=prompt_hash,
                schema=schema.__name__,
            )
            return TaskResult.success(instance)
        except json.JSONDecodeError as e:
            return TaskResult.failure(f"Invalid JSON: {e}")
        except ValidationError as e:
            return TaskResult.failure(f"Schema validation failed: {e}")

    async def check_model_available(self) -> bool:
        """Check if configured model is available."""
        if self.provider == "ollama":
            base_url = str(self.config.get("base_url", "http://localhost:11434/v1"))
            model = self._get_model_name()
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(base_url.replace("/v1", "/api/tags"))
                    if response.status_code == 200:
                        models = [m.get("name", "") for m in response.json().get("models", [])]
                        return model in models
            except Exception:
                return False
        # For OpenRouter, assume available if key is set
        return bool(self.config.get("api_key"))
