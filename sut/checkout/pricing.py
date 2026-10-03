"""Checkout pricing. Each rule carries the acceptance criterion it implements
(stories/*.md) in a trailing comment; the mutation engine uses those tags to
know which criterion a mutant breaks."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from .models import CartError, Coupon, CouponError, Customer, Line, Product, Quote

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def _cents(x: Decimal) -> Decimal:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)  # S6-AC2


def _merge(lines: list[Line], catalog: dict[str, Product]) -> dict[str, int]:
    merged: dict[str, int] = {}
    for line in lines:
        if not isinstance(line.quantity, int) or isinstance(line.quantity, bool):  # S1-AC2
            raise CartError(f"quantity must be a whole number: {line.quantity!r}")  # S1-AC2
        if line.quantity < 1 or line.quantity > 99:  # S1-AC2
            raise CartError(f"quantity out of range: {line.quantity}")  # S1-AC2
        if line.sku not in catalog:  # S1-AC3
            raise CartError(f"unknown product: {line.sku}")  # S1-AC3
        merged[line.sku] = merged.get(line.sku, 0) + line.quantity  # S1-AC4
    for sku, quantity in merged.items():
        if quantity > 99:  # S1-AC4
            raise CartError(f"more than 99 units of {sku}")  # S1-AC4
    return merged


def _volume_rate(product: Product, quantity: int) -> Decimal:
    if product.category == "books":  # S2-AC3
        return Decimal("0")  # S2-AC3
    if quantity >= 50:  # S2-AC2
        return Decimal("0.15")  # S2-AC2
    if quantity >= 10:  # S2-AC1
        return Decimal("0.10")  # S2-AC1
    return Decimal("0")  # S2-AC1


def _check_coupon(coupon: Coupon, subtotal: Decimal, today: date) -> None:
    if coupon.kind not in ("percent", "fixed"):  # S3-AC5
        raise CouponError(f"unknown coupon kind: {coupon.kind}")  # S3-AC5
    if coupon.expires is not None and today > coupon.expires:  # S3-AC4
        raise CouponError(f"coupon {coupon.code} expired on {coupon.expires}")  # S3-AC4
    if subtotal < coupon.min_subtotal:  # S3-AC3
        raise CouponError(f"coupon {coupon.code} needs a subtotal of {coupon.min_subtotal}")  # S3-AC3


def price_cart(
    lines: list[Line],
    catalog: dict[str, Product],
    *,
    today: date,
    customer: Customer = Customer(),
    coupon: Coupon | None = None,
    shipping: str = "standard",
) -> Quote:
    merged = _merge(lines, catalog)
    if shipping not in ("standard", "express"):  # S5-AC3
        raise CartError(f"unknown shipping method: {shipping}")  # S5-AC3
    if not merged:  # S1-AC5
        return Quote(ZERO, ZERO, ZERO, ZERO, ZERO, ())  # S1-AC5

    applied: list[str] = []
    raw = Decimal("0")  # S1-AC1
    for sku, quantity in merged.items():
        product = catalog[sku]
        line_total = product.unit_price * quantity  # S1-AC1
        rate = _volume_rate(product, quantity)
        if rate > 0:  # S2-AC1
            line_total -= line_total * rate  # S2-AC1
            applied.append(f"volume:{sku}")  # S6-AC3
        raw += line_total  # S1-AC1
    subtotal = _cents(raw)  # S6-AC2

    if coupon is not None:  # S3-AC3
        _check_coupon(coupon, subtotal, today)  # S3-AC3

    # Loyalty and a percent coupon don't stack: the larger one applies, the coupon on a tie.
    loyalty = _cents(subtotal * Decimal("0.05")) if customer.tier == "gold" else ZERO  # S4-AC1
    percent = ZERO
    if coupon is not None and coupon.kind == "percent":  # S3-AC1
        percent = _cents(subtotal * coupon.value / 100)  # S3-AC1
    if loyalty > percent:  # S4-AC2
        rate_discount = loyalty  # S4-AC2
        applied.append("loyalty")  # S6-AC3
    elif percent > 0:  # S4-AC2
        rate_discount = percent  # S4-AC2
        applied.append(f"coupon:{coupon.code}")  # S6-AC3
    else:
        rate_discount = ZERO

    # A fixed coupon stacks on top, and never takes the goods below zero.
    fixed = ZERO
    if coupon is not None and coupon.kind == "fixed":  # S3-AC2
        fixed = min(coupon.value, subtotal - rate_discount)  # S3-AC2
        applied.append(f"coupon:{coupon.code}")  # S6-AC3
    discount = rate_discount + fixed  # S3-AC2
    goods = subtotal - discount  # S3-AC2

    if shipping == "express":  # S5-AC2
        ship = Decimal("9.99")  # S5-AC2
    elif goods >= Decimal("50.00"):  # S5-AC1
        ship = ZERO  # S5-AC1
    else:
        ship = Decimal("4.99")  # S5-AC1

    tax = _cents((goods + ship) * Decimal("0.21"))  # S6-AC1
    total = goods + ship + tax  # S6-AC2
    return Quote(_cents(subtotal), _cents(discount), _cents(ship), tax, _cents(total), tuple(applied))
