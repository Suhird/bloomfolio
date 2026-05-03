"""Prompt builders for agent analysis."""

from __future__ import annotations

from typing import Any

from bloomfolio.domain.portfolio import Holding, Portfolio


def build_fundamental_prompt(ticker: str, holding: Holding | None, market_data: dict[str, str]) -> str:
    """Build fundamental analysis prompt."""
    portfolio_context = ""
    if holding:
        portfolio_context = f"""
User Portfolio Context:
- Ticker: {ticker}
- Quantity: {holding.quantity}
- Currency: {holding.currency}
- Account: {holding.account_name}
- Market Value: {holding.market_value or 'N/A'}
- Book Cost: {holding.book_cost or 'N/A'}
"""

    return f"""Analyze the fundamentals of {ticker}.

{portfolio_context}

Market Data Context:
{market_data}

Instructions:
1. Do not invent data. Use only the provided context.
2. Provide a concise summary of financial health.
3. List 2-3 strengths and 2-3 weaknesses.
4. Give a brief valuation assessment.
5. Output valid JSON matching the FundamentalAnalysis schema.
6. Include uncertainty about missing data.

Do not provide personalized financial advice. This is research analysis only.
"""


def build_technical_prompt(ticker: str, market_data: dict[str, str]) -> str:
    """Build technical analysis prompt."""
    return f"""Analyze the technical indicators for {ticker}.

Market Data Context:
{market_data}

Instructions:
1. Describe the current trend (bullish/bearish/sideways).
2. List key support and resistance levels if available.
3. Mention important technical indicators.
4. Output valid JSON matching the TechnicalAnalysis schema.
5. Do not invent price targets or guaranteed outcomes.

Do not provide personalized financial advice.
"""


def build_news_prompt(ticker: str, news_items: list[dict[str, Any]]) -> str:
    """Build news analysis prompt."""
    news_context = "\n".join([f"- {n.get('title', '')}" for n in news_items[:5]])
    return f"""Analyze recent news for {ticker}.

Recent Headlines:
{news_context}

Instructions:
1. Summarize the news sentiment.
2. List key catalysts or risks from recent news.
3. Output valid JSON matching the NewsAnalysis schema.
4. Note if news data is limited or stale.

Do not provide personalized financial advice.
"""


def build_sentiment_prompt(ticker: str, sentiment_data: dict[str, str]) -> str:
    """Build sentiment analysis prompt."""
    return f"""Analyze market sentiment for {ticker}.

Sentiment Data:
{sentiment_data}

Instructions:
1. Assess overall sentiment (bullish/bearish/neutral).
2. Provide a sentiment score from -1 to 1.
3. Output valid JSON matching the SentimentAnalysis schema.
4. Note data limitations and uncertainty.

Do not provide personalized financial advice.
"""


def build_bull_prompt(ticker: str, analyses: dict[str, object]) -> str:
    """Build bull researcher prompt."""
    return f"""You are a bullish researcher analyzing {ticker}.

Available Analysis:
{analyses}

Instructions:
1. Present the strongest bull case.
2. List key arguments and upside scenarios.
3. Rate your confidence (0-1).
4. Output valid JSON matching the BullCase schema.
5. Acknowledge uncertainties and risks even while making the bull case.

Do not provide personalized financial advice.
"""


def build_bear_prompt(ticker: str, analyses: dict[str, object]) -> str:
    """Build bear researcher prompt."""
    return f"""You are a bearish researcher analyzing {ticker}.

Available Analysis:
{analyses}

Instructions:
1. Present the strongest bear case.
2. List key arguments and downside scenarios.
3. Rate your confidence (0-1).
4. Output valid JSON matching the BearCase schema.
5. Acknowledge potential positives even while making the bear case.

Do not provide personalized financial advice.
"""


def build_trader_prompt(ticker: str, bull_case: dict[str, object], bear_case: dict[str, object], analyses: dict[str, object]) -> str:
    """Build trader synthesis prompt."""
    return f"""You are a trader synthesizing research on {ticker}.

Bull Case:
{bull_case}

Bear Case:
{bear_case}

Other Analysis:
{analyses}

Instructions:
1. Synthesize all research into a concise summary.
2. Provide a rating: strong_bearish, bearish, neutral, bullish, strong_bullish.
3. Provide an action label: watch, research_more, rebalance_candidate, risk_review, no_action.
4. Specify time horizon: short, medium, long.
5. Rate confidence (0-1).
6. Output valid JSON matching the TraderSynthesis schema.

Use research labels only. Do not say "buy" or "sell".
Do not provide personalized financial advice.
"""


def build_risk_prompt(ticker: str, holding: Holding | None, analyses: dict[str, object]) -> str:
    """Build risk review prompt."""
    portfolio_context = ""
    if holding:
        portfolio_context = f"""
Portfolio Context:
- Position size: {holding.quantity} shares
- Market value: {holding.market_value or 'N/A'} {holding.currency}
- Book cost: {holding.book_cost or 'N/A'} {holding.currency}
"""

    return f"""You are a risk manager reviewing {ticker}.

{portfolio_context}

Research Analysis:
{analyses}

Instructions:
1. Identify key risk factors.
2. Assess risk level: low, medium, high, extreme.
3. Suggest mitigation notes.
4. Output valid JSON matching the RiskReview schema.

Do not provide personalized financial advice.
"""


def build_portfolio_manager_prompt(
    ticker: str,
    holding: Holding | None,
    portfolio: Portfolio | None,
    trader_synthesis: dict[str, object],
    risk_review: dict[str, object],
) -> str:
    """Build portfolio manager conclusion prompt."""
    portfolio_context = ""
    if portfolio and holding:
        totals = portfolio.get_total_value()
        portfolio_context = f"""
Portfolio Context:
- Total portfolio value: {totals}
- This holding: {holding.ticker} in {holding.account_name}
- Quantity: {holding.quantity}
- Weight: {holding.portfolio_weight or 'N/A'}
"""

    return f"""You are a portfolio manager making a final research conclusion on {ticker}.

Trader Synthesis:
{trader_synthesis}

Risk Review:
{risk_review}

{portfolio_context}

Instructions:
1. Provide final rating: strong_bearish, bearish, neutral, bullish, strong_bullish.
2. Provide final action label: watch, research_more, rebalance_candidate, risk_review, no_action.
3. Summarize thesis, bull case, bear case.
4. List risk notes and portfolio context observations.
5. List key uncertainties.
6. Rate confidence (0-1).
7. Output valid JSON matching the PortfolioManagerConclusion schema.

This is research analysis only. Do not provide personalized financial advice.
Include disclaimer: "This analysis is for research purposes only..."
"""
