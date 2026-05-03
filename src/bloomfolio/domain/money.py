"""Money value object."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class Money(BaseModel):
    """Money value object with currency."""

    amount: Decimal
    currency: Literal["CAD", "USD"]

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:,.2f}"

    def add(self, other: Money) -> Money:
        """Add two money values. Must be same currency."""
        if self.currency != other.currency:
            msg = f"Cannot add {self.currency} and {other.currency}"
            raise ValueError(msg)
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def subtract(self, other: Money) -> Money:
        """Subtract two money values. Must be same currency."""
        if self.currency != other.currency:
            msg = f"Cannot subtract {self.currency} and {other.currency}"
            raise ValueError(msg)
        return Money(amount=self.amount - other.amount, currency=self.currency)

    @classmethod
    def from_string(cls, value: str, currency: Literal["CAD", "USD"] = "CAD") -> Money:
        """Parse money from string."""
        clean = value.replace("$", "").replace(",", "").strip()
        return Money(amount=Decimal(clean), currency=currency)
