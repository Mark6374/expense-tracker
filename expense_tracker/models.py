from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date
from decimal import Decimal, InvalidOperation
from typing import Any

CENT = Decimal("0.01")


class ValidationError(ValueError):
    """Raised for invalid user input or invalid stored records."""


def parse_amount(raw: object) -> Decimal:
    """Return a positive amount with exactly two decimal places."""
    try:
        value = Decimal(str(raw).strip())
    except InvalidOperation:
        raise ValidationError(f"invalid amount {raw!r}: use digits and '.', e.g. 12.50") from None
    if not value.is_finite() or value <= 0:
        raise ValidationError(f"invalid amount {raw!r}: must be a positive number")
    if value != value.quantize(CENT):
        raise ValidationError(f"invalid amount {raw!r}: at most 2 decimal places")
    return value.quantize(CENT)


def parse_date(raw: object) -> str:
    """Return the date in ISO format (YYYY-MM-DD)."""
    try:
        return _date.fromisoformat(str(raw)).isoformat()
    except ValueError:
        raise ValidationError(f"invalid date {raw!r}: expected YYYY-MM-DD") from None


@dataclass
class Expense:
    date: str
    category: str
    description: str
    amount: Decimal

    def __post_init__(self) -> None:
        self.date = parse_date(self.date)
        self.amount = parse_amount(self.amount)

    def to_dict(self) -> dict[str, str]:
        # Amount is stored as a string so no precision is lost in JSON.
        return {
            "date": self.date,
            "category": self.category,
            "description": self.description,
            "amount": str(self.amount),
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> Expense:
        try:
            return Expense(d["date"], d["category"], d["description"], d["amount"])
        except (KeyError, TypeError) as exc:
            raise ValidationError(f"malformed record {d!r}: missing field {exc}") from None
