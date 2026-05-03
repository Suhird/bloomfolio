"""Portfolio domain models."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from bloomfolio.domain.enums import AssetType
from bloomfolio.domain.money import Money


class Holding(BaseModel):
    """A single portfolio holding."""

    ticker: str
    security_name: str | None = None
    quantity: Decimal
    currency: Literal["CAD", "USD"]
    account_name: str
    market_value: Decimal | None = None
    book_cost: Decimal | None = None
    average_cost: Decimal | None = None
    current_price: Decimal | None = None
    asset_type: AssetType = AssetType.UNKNOWN
    exchange: str | None = None
    sector: str | None = None
    country: str | None = None
    portfolio_weight: Decimal | None = None
    unrealized_gain_loss: Decimal | None = None
    unrealized_gain_loss_pct: Decimal | None = None
    source_row_number: int = 0

    def get_market_value_money(self) -> Money | None:
        """Get market value as Money object."""
        if self.market_value is not None:
            return Money(amount=self.market_value, currency=self.currency)
        return None

    def get_book_cost_money(self) -> Money | None:
        """Get book cost as Money object."""
        if self.book_cost is not None:
            return Money(amount=self.book_cost, currency=self.currency)
        return None

    def is_cash(self) -> bool:
        """Check if this is a cash holding."""
        return self.asset_type == AssetType.CASH or self.ticker.strip().upper() == "CASH"


class Portfolio(BaseModel):
    """A portfolio import."""

    id: UUID = Field(default_factory=uuid4)
    imported_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_file_name: str = ""
    holdings: list[Holding] = Field(default_factory=list)
    base_currency: Literal["CAD", "USD"] = "CAD"

    def get_total_value(self, currency: Literal["CAD", "USD"] | None = None) -> dict[str, Money]:
        """Get total portfolio value per currency."""
        totals: dict[str, Decimal] = {"CAD": Decimal("0"), "USD": Decimal("0")}
        for holding in self.holdings:
            if holding.market_value is not None:
                totals[holding.currency] += holding.market_value

        result: dict[str, Money] = {}
        for ccy, amount in totals.items():
            if amount > 0:
                result[ccy] = Money(amount=amount, currency=ccy)  # type: ignore[arg-type]
        return result

    def get_tickers(self) -> list[str]:
        """Get all non-cash tickers."""
        return [h.ticker for h in self.holdings if not h.is_cash()]

    def get_cash_holdings(self) -> list[Holding]:
        """Get cash holdings."""
        return [h for h in self.holdings if h.is_cash()]

    def get_non_cash_holdings(self) -> list[Holding]:
        """Get non-cash holdings."""
        return [h for h in self.holdings if not h.is_cash()]
