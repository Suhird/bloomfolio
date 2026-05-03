"""Export functionality for reports."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bloomfolio.domain.portfolio import Portfolio
from bloomfolio.domain.reports import TickerAnalysisResult
from bloomfolio.observability.logging import get_logger

logger = get_logger(__name__)

DISCLAIMER = (
    "> **Disclaimer:** This application is for research and educational analysis only. "
    "It does not provide financial, investment, tax, or trading advice. "
    "AI-generated outputs may be incomplete, stale, or wrong. "
    "Always verify data independently and consult a qualified professional before making financial decisions."
)


def export_portfolio_markdown(
    portfolio: Portfolio,
    results: dict[str, TickerAnalysisResult],
    output_path: Path,
) -> Path:
    """Export portfolio analysis to Markdown.

    Args:
        portfolio: Portfolio to export.
        results: Analysis results by ticker.
        output_path: Output file path.

    Returns:
        Path to exported file.
    """
    lines = [
        "# BloomFolio Portfolio Analysis Report",
        "",
        f"Generated: {datetime.now(UTC).isoformat()}",
        f"Source: {portfolio.source_file_name}",
        f"Holdings: {len(portfolio.holdings)}",
        "",
        DISCLAIMER,
        "",
        "---",
        "",
        "## Holdings Summary",
        "",
        "| Ticker | Name | Quantity | Currency | Account | Value |",
        "|--------|------|----------|----------|---------|-------|",
    ]

    for h in portfolio.holdings:
        lines.append(
            f"| {h.ticker} | {h.security_name or ''} | {h.quantity} | "
            f"{h.currency} | {h.account_name} | {h.market_value or '-'} |"
        )

    lines.extend(["", "---", "", "## Ticker Analysis", ""])

    for ticker, result in results.items():
        lines.extend(_format_ticker_markdown(ticker, result))

    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("markdown_export_complete", path=str(output_path), tickers=len(results))
    return output_path


def _format_ticker_markdown(ticker: str, result: TickerAnalysisResult) -> list[str]:
    """Format single ticker analysis as markdown lines."""
    lines = [f"### {ticker}", ""]

    if result.errors:
        lines.append(f"**Errors:** {', '.join(result.errors)}")
        lines.append("")

    for report in result.reports:
        lines.append(f"#### {report.agent_name}")
        lines.append(f"- **Stage:** {report.stage.value}")
        lines.append(f"- **Confidence:** {report.confidence:.0%}")
        lines.append(f"- **Summary:** {report.summary}")
        if report.key_points:
            lines.append("- **Key Points:**")
            for point in report.key_points:
                lines.append(f"  - {point}")
        lines.append("")

    if result.decision:
        d = result.decision
        lines.append("#### Final Decision")
        lines.append(f"- **Rating:** {d.rating.value}")
        lines.append(f"- **Action:** {d.action_label.value}")
        lines.append(f"- **Time Horizon:** {d.time_horizon.value}")
        lines.append(f"- **Confidence:** {d.confidence:.0%}")
        lines.append(f"- **Thesis:** {d.thesis}")
        if d.risk_notes:
            lines.append("- **Risk Notes:**")
            for note in d.risk_notes:
                lines.append(f"  - {note}")
        lines.append("")

    return lines


def export_portfolio_json(
    portfolio: Portfolio,
    results: dict[str, TickerAnalysisResult],
    output_path: Path,
) -> Path:
    """Export portfolio analysis to JSON.

    Args:
        portfolio: Portfolio to export.
        results: Analysis results by ticker.
        output_path: Output file path.

    Returns:
        Path to exported file.
    """
    data: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source": portfolio.source_file_name,
        "portfolio": portfolio.model_dump(),
        "results": {t: r.model_dump() for t, r in results.items()},
        "disclaimer": DISCLAIMER,
    }

    output_path.write_text(
        json.dumps(data, indent=2, default=str),
        encoding="utf-8",
    )
    logger.info("json_export_complete", path=str(output_path), tickers=len(results))
    return output_path
