"""Quick smoke-test for LLM inference via OpenRouter."""

from __future__ import annotations

import asyncio

from pydantic import BaseModel

from bloomfolio.llm.client import ChatMessage, LLMGateway


class SmokeTestOutput(BaseModel):
    """Simple schema for testing JSON structured output."""

    ticker: str
    summary: str
    rating: str


async def main() -> None:
    gateway = LLMGateway()
    print(f"Provider: {gateway.provider}")
    print(f"Model: {gateway._get_model_name()}")
    print(f"Base URL: {gateway.config.get('base_url')}")
    print("-" * 40)

    messages = [
        ChatMessage(
            role="user",
            content=(
                "Analyze ticker AAPL in one sentence. "
                "Output valid JSON with fields: ticker (string), summary (string), rating (string)."
            ),
        )
    ]

    print("Sending request...")
    try:
        result = await gateway.complete_json(
            messages=messages,
            schema=SmokeTestOutput,
            temperature=0.3,
            timeout_seconds=60,
        )
        print("SUCCESS!")
        print(f"  ticker: {result.ticker}")
        print(f"  summary: {result.summary}")
        print(f"  rating: {result.rating}")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
