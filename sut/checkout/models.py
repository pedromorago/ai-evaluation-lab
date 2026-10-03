from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


class CartError(ValueError):
    """The cart can't be priced: a bad quantity, an unknown product or shipping method."""


class CouponError(CartError):
    """The coupon can't be applied to this cart."""


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    unit_price: Decimal
    category: str = "general"  # "general" or "books"


@dataclass(frozen=True)
class Line:
    sku: str
    quantity: int


@dataclass(frozen=True)
class Customer:
    tier: str = "standard"  # "standard" or "gold"


@dataclass(frozen=True)
class Coupon:
    code: str
    kind: str  # "percent" or "fixed"
    value: Decimal  # percent: 10 means 10% off; fixed: an amount in euros
    min_subtotal: Decimal = Decimal("0")
    expires: date | None = None  # last day the coupon is valid


@dataclass(frozen=True)
class Quote:
    subtotal: Decimal  # line totals after volume discounts
    discount: Decimal  # coupon and loyalty discounts
    shipping: Decimal
    tax: Decimal
    total: Decimal
    applied: tuple[str, ...]  # what was applied, e.g. ("volume:BK-1", "loyalty", "coupon:SAVE10")
