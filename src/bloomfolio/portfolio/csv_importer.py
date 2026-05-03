"""CSV importer for Wealthsimple portfolio exports."""

from __future__ import annotations

import asyncio
import csv
from decimal import Decimal
from pathlib import Path

from bloomfolio.domain.enums import AssetType
from bloomfolio.domain.portfolio import Holding, Portfolio
from bloomfolio.observability.logging import get_logger
from bloomfolio.portfolio.normalizer import normalize_columns
from bloomfolio.portfolio.validator import validate_csv_file

logger = get_logger(__name__)


async def import_csv(path: str) -> Portfolio:
    """Import a portfolio CSV file.

    Args:
        path: Path to CSV file.

    Returns:
        Portfolio domain object.

    Raises:
        PortfolioValidationError: If CSV is invalid.
    """
    logger.info("csv_import_starting", path=Path(path).name)

    # Run validation first
    validation = await validate_csv_file(path)
    if not validation.valid:
        from bloomfolio.domain.exceptions import PortfolioValidationError

        errors = [e.message for e in validation.errors if e.severity == "ERROR"]
        raise PortfolioValidationError(f"CSV validation failed: {'; '.join(errors[:3])}")

    # Read and parse CSV
    loop = asyncio.get_event_loop()

    def _read() -> Portfolio:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValueError("CSV has no header row")

            normalized = normalize_columns(list(reader.fieldnames))
            holdings: list[Holding] = []

            for i, row in enumerate(reader, start=2):
                # Skip empty rows / Wealthsimple footer rows
                if _is_empty_row(row, normalized):
                    continue
                try:
                    holding = _row_to_holding(row, normalized, i)
                    holdings.append(holding)
                except Exception as e:
                    logger.warning(
                        "csv_row_parse_failed",
                        row=i,
                        error=str(e),
                    )

        return Portfolio(
            source_file_name=Path(path).name,
            holdings=holdings,
        )

    portfolio = await loop.run_in_executor(None, _read)
    logger.info(
        "csv_import_complete",
        holdings=len(portfolio.holdings),
        file=Path(path).name,
    )
    return portfolio


def _row_to_holding(
    row: dict[str, str],
    normalized: dict[str, str],
    row_number: int,
) -> Holding:
    """Convert a CSV row to a Holding."""
    ticker = (_get_field(row, normalized, "ticker", "") or "").strip()
    quantity_str = _get_field(row, normalized, "quantity", "0")
    currency = (_get_field(row, normalized, "currency", "CAD") or "CAD").strip().upper()
    account_name = (_get_field(row, normalized, "account_name", "") or "").strip()

    if not ticker:
        raise ValueError("Empty ticker")
    if not account_name:
        raise ValueError("Empty account_name")

    quantity = Decimal(quantity_str) if quantity_str else Decimal("0")
    if quantity < 0:
        raise ValueError("Negative quantity")

    asset_type_str = (_get_field(row, normalized, "asset_type", "") or "").strip().lower()
    asset_type = _map_asset_type(asset_type_str)

    market_value = _parse_decimal(_get_field(row, normalized, "market_value", ""))
    book_cost = _parse_decimal(_get_field(row, normalized, "book_cost", ""))
    average_cost = _parse_decimal(_get_field(row, normalized, "average_cost", ""))
    current_price = _parse_decimal(_get_field(row, normalized, "current_price", ""))
    portfolio_weight = _parse_percentage(_get_field(row, normalized, "portfolio_weight", ""))
    unrealized_gl = _parse_decimal(_get_field(row, normalized, "unrealized_gain_loss", ""))
    unrealized_gl_pct = _parse_percentage(
        _get_field(row, normalized, "unrealized_gain_loss_pct", "")
    )

    return Holding(
        ticker=ticker,
        security_name=_get_field(row, normalized, "security_name", None),
        quantity=quantity,
        currency=currency,  # type: ignore[arg-type]
        account_name=account_name,
        market_value=market_value,
        book_cost=book_cost,
        average_cost=average_cost,
        current_price=current_price,
        asset_type=asset_type,
        exchange=_get_field(row, normalized, "exchange", None),
        sector=_get_field(row, normalized, "sector", None),
        country=_get_field(row, normalized, "country", None),
        portfolio_weight=portfolio_weight,
        unrealized_gain_loss=unrealized_gl,
        unrealized_gain_loss_pct=unrealized_gl_pct,
        source_row_number=row_number,
    )


def _map_asset_type(raw: str) -> AssetType:
    """Map Wealthsimple asset type strings to AssetType enum."""
    if not raw:
        return AssetType.UNKNOWN
    mapping: dict[str, AssetType] = {
        "exchange_traded_fund": AssetType.ETF,
        "equity": AssetType.STOCK,
        "precious_metal": AssetType.OTHER,
        "mutual_fund": AssetType.OTHER,
        "fixed_income": AssetType.BOND,
        "bond": AssetType.BOND,
        "cash": AssetType.CASH,
        "crypto": AssetType.CRYPTO,
    }
    return mapping.get(raw, AssetType.UNKNOWN)


def _is_empty_row(
    row: dict[str, str],
    normalized: dict[str, str],
) -> bool:
    """Skip rows with no ticker and no quantity (empty/footer rows)."""
    ticker = ""
    quantity = ""
    for raw, canonical in normalized.items():
        value = (row.get(raw) or "").strip()
        if canonical == "ticker":
            ticker = value
        elif canonical == "quantity":
            quantity = value
    return ticker == "" and quantity == ""


def _get_field(
    row: dict[str, str],
    normalized: dict[str, str],
    canonical: str,
    default: str | None,
) -> str | None:
    """Get a field from row using normalized column mapping."""
    for raw, norm in normalized.items():
        if norm == canonical and raw in row:
            value = row[raw].strip()
            return value if value else default
    return default


def _parse_decimal(value: str | None) -> Decimal | None:
    """Parse decimal value, return None if empty."""
    if not value:
        return None
    try:
        clean = value.replace("$", "").replace(",", "").replace("%", "").strip()
        return Decimal(clean)
    except Exception:
        return None


def _parse_percentage(value: str | None) -> Decimal | None:
    """Parse percentage value, return None if empty."""
    if not value:
        return None
    try:
        clean = value.replace("$", "").replace(",", "").strip()
        if clean.endswith("%"):
            clean = clean[:-1]
            return Decimal(clean) / Decimal("100")
        val = Decimal(clean)
        if val > 1:
            return val / Decimal("100")
        return val
    except Exception:
        return None
