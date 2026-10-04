from datetime import date, timedelta
from decimal import Decimal

import pytest

from checkout import (
    CartError,
    Coupon,
    CouponError,
    Customer,
    Line,
    Product,
    price_cart,
)

TODAY = date(2026, 6, 15)

CATALOG = {
    "GEN-100": Product("GEN-100", "Hundred", Decimal("100.00")),
    "GEN-20": Product("GEN-20", "Twenty", Decimal("20.00")),
    "GEN-10": Product("GEN-10", "Ten", Decimal("10.00")),
    "GEN-10-05": Product("GEN-10-05", "Ten oh five", Decimal("10.05")),
    "GEN-49": Product("GEN-49", "Under fifty", Decimal("49.99")),
    "GEN-50": Product("GEN-50", "Fifty", Decimal("50.00")),
}


def price(lines, coupon=None, **kwargs):
    kwargs.setdefault("today", TODAY)
    return price_cart(lines, CATALOG, coupon=coupon, **kwargs)


def pct(value, code="PCT", **kw):
    return Coupon(code=code, kind="percent", value=Decimal(str(value)), **kw)


def fixed(value, code="FIX", **kw):
    return Coupon(code=code, kind="fixed", value=Decimal(str(value)), **kw)


# ---------------------------------------------------------------- S3-AC1

@pytest.mark.ac("S3-AC1")
def test_percent_coupon_takes_percentage_off_subtotal():
    q = price([Line("GEN-100", 1)], pct(10, "SAVE10"))
    assert q.subtotal == Decimal("100.00")
    assert q.discount == Decimal("10.00")
    assert q.applied == ("coupon:SAVE10",)
    # goods 90.00 -> free shipping, tax 18.90
    assert q.shipping == Decimal("0.00")
    assert q.tax == Decimal("18.90")
    assert q.total == Decimal("108.90")


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_value_is_a_percentage_not_a_fraction():
    q = price([Line("GEN-100", 1)], pct(25, "QUARTER"))
    assert q.discount == Decimal("25.00")


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_discount_rounded_half_up():
    # 10% of 10.05 = 1.005 -> 1.01
    q = price([Line("GEN-10-05", 1)], pct(10))
    assert q.subtotal == Decimal("10.05")
    assert q.discount == Decimal("1.01")


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_of_100_takes_everything_off():
    q = price([Line("GEN-20", 1)], pct(100, "FREE"))
    assert q.discount == Decimal("20.00")


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_applies_to_subtotal_after_volume_discount():
    # 10 x 10.00 = 100.00, volume 10% -> subtotal 90.00; coupon 10% -> 9.00
    q = price([Line("GEN-10", 10)], pct(10))
    assert q.subtotal == Decimal("90.00")
    assert q.discount == Decimal("9.00")


# ---------------------------------------------------------------- S3-AC2

@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_takes_euros_off():
    q = price([Line("GEN-100", 1)], fixed(5, "FIVE"))
    assert q.subtotal == Decimal("100.00")
    assert q.discount == Decimal("5.00")
    assert q.applied == ("coupon:FIVE",)
    # goods 95.00 -> free shipping, tax 19.95
    assert q.shipping == Decimal("0.00")
    assert q.tax == Decimal("19.95")
    assert q.total == Decimal("114.95")


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_never_takes_goods_below_zero():
    q = price([Line("GEN-20", 1)], fixed(50, "BIG"))
    assert q.subtotal == Decimal("20.00")
    assert q.discount == Decimal("20.00")
    # goods are 0.00: only standard shipping 4.99 and its VAT remain
    assert q.shipping == Decimal("4.99")
    assert q.tax == Decimal("1.05")
    assert q.total == Decimal("6.04")


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_equal_to_goods_brings_them_to_exactly_zero():
    q = price([Line("GEN-20", 1)], fixed(20))
    assert q.discount == Decimal("20.00")
    assert q.total == q.shipping + q.tax


@pytest.mark.ac("S3-AC2", "S4-AC2")
def test_fixed_coupon_is_taken_off_after_loyalty_discount():
    q = price([Line("GEN-100", 1)], fixed(10, "TEN"), customer=Customer(tier="gold"))
    # loyalty 5.00 + fixed 10.00
    assert q.discount == Decimal("15.00")
    assert q.applied == ("loyalty", "coupon:TEN")


@pytest.mark.ac("S3-AC2", "S4-AC2")
def test_fixed_coupon_after_loyalty_is_capped_at_remaining_goods():
    q = price([Line("GEN-20", 1)], fixed(50, "BIG"), customer=Customer(tier="gold"))
    # loyalty 1.00, fixed capped at the remaining 19.00 -> total discount 20.00
    assert q.discount == Decimal("20.00")
    assert q.total == q.subtotal - q.discount + q.shipping + q.tax


# ---------------------------------------------------------------- S3-AC3

@pytest.mark.ac("S3-AC3")
def test_subtotal_below_minimum_raises():
    coupon = pct(10, min_subtotal=Decimal("50.00"))
    with pytest.raises(CouponError):
        price([Line("GEN-49", 1)], coupon)


@pytest.mark.ac("S3-AC3")
def test_subtotal_equal_to_minimum_is_enough():
    coupon = pct(10, min_subtotal=Decimal("50.00"))
    q = price([Line("GEN-50", 1)], coupon)
    assert q.discount == Decimal("5.00")


@pytest.mark.ac("S3-AC3")
def test_subtotal_above_minimum_is_accepted():
    coupon = pct(10, min_subtotal=Decimal("50.00"))
    q = price([Line("GEN-100", 1)], coupon)
    assert q.discount == Decimal("10.00")


@pytest.mark.ac("S3-AC3")
def test_minimum_applies_to_fixed_coupons_too():
    with pytest.raises(CouponError):
        price([Line("GEN-49", 1)], fixed(5, min_subtotal=Decimal("50.00")))
    q = price([Line("GEN-50", 1)], fixed(5, min_subtotal=Decimal("50.00")))
    assert q.discount == Decimal("5.00")


@pytest.mark.ac("S3-AC3")
def test_minimum_is_checked_against_subtotal_after_volume_discount():
    # 10 x 10.00 = 100.00 -> 90.00 after the volume discount
    coupon = pct(10, min_subtotal=Decimal("95.00"))
    with pytest.raises(CouponError):
        price([Line("GEN-10", 10)], coupon)
    ok = pct(10, min_subtotal=Decimal("90.00"))
    assert price([Line("GEN-10", 10)], ok).discount == Decimal("9.00")


@pytest.mark.ac("S3-AC3")
def test_coupon_error_for_minimum_is_a_cart_error():
    coupon = pct(10, min_subtotal=Decimal("50.00"))
    with pytest.raises(CartError):
        price([Line("GEN-49", 1)], coupon)


# ---------------------------------------------------------------- S3-AC4

@pytest.mark.ac("S3-AC4")
def test_expired_coupon_raises():
    coupon = pct(10, expires=TODAY - timedelta(days=1))
    with pytest.raises(CouponError):
        price([Line("GEN-100", 1)], coupon)


@pytest.mark.ac("S3-AC4")
def test_coupon_is_valid_on_its_expiry_date():
    coupon = pct(10, expires=TODAY)
    q = price([Line("GEN-100", 1)], coupon)
    assert q.discount == Decimal("10.00")


@pytest.mark.ac("S3-AC4")
def test_coupon_before_expiry_is_valid():
    coupon = pct(10, expires=TODAY + timedelta(days=30))
    q = price([Line("GEN-100", 1)], coupon)
    assert q.discount == Decimal("10.00")


@pytest.mark.ac("S3-AC4")
def test_coupon_without_expiry_never_expires():
    coupon = pct(10, expires=None)
    q = price([Line("GEN-100", 1)], coupon, today=date(2099, 12, 31))
    assert q.discount == Decimal("10.00")


@pytest.mark.ac("S3-AC4")
def test_expiry_is_judged_against_the_today_argument():
    coupon = fixed(5, expires=date(2026, 6, 15))
    assert price([Line("GEN-100", 1)], coupon, today=date(2026, 6, 15)).discount == Decimal("5.00")
    with pytest.raises(CouponError):
        price([Line("GEN-100", 1)], coupon, today=date(2026, 6, 16))


@pytest.mark.ac("S3-AC4")
def test_expired_fixed_coupon_raises():
    coupon = fixed(5, expires=TODAY - timedelta(days=1))
    with pytest.raises(CouponError):
        price([Line("GEN-100", 1)], coupon)


# ---------------------------------------------------------------- S3-AC5

@pytest.mark.ac("S3-AC5")
def test_unknown_coupon_kind_raises():
    coupon = Coupon(code="ODD", kind="bogus", value=Decimal("10"))
    with pytest.raises(CouponError):
        price([Line("GEN-100", 1)], coupon)


@pytest.mark.ac("S3-AC5")
def test_empty_coupon_kind_raises():
    coupon = Coupon(code="ODD", kind="", value=Decimal("10"))
    with pytest.raises(CouponError):
        price([Line("GEN-100", 1)], coupon)


@pytest.mark.ac("S3-AC5")
def test_coupon_error_is_a_cart_error_and_value_error():
    assert issubclass(CouponError, CartError)
    assert issubclass(CouponError, ValueError)
    coupon = Coupon(code="ODD", kind="bogus", value=Decimal("10"))
    with pytest.raises(CartError):
        price([Line("GEN-100", 1)], coupon)
