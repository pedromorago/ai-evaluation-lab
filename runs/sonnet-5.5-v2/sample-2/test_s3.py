from datetime import date
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

TODAY = date(2025, 6, 15)


def D(value: str) -> Decimal:
    return Decimal(value)


def catalog_for(price: str, category: str = "general") -> dict:
    return {"A": Product(sku="A", name="Product A", unit_price=D(price), category=category)}


def quote_single(price: str, coupon=None, qty: int = 1, customer=None, today=TODAY, category="general"):
    kwargs = {"today": today, "coupon": coupon}
    if customer is not None:
        kwargs["customer"] = customer
    return price_cart([Line("A", qty)], catalog_for(price, category), **kwargs)


# ---------------------------------------------------------------- S3-AC1

@pytest.mark.ac("S3-AC1")
def test_percent_coupon_10_takes_10_percent_off_subtotal():
    coupon = Coupon(code="SAVE10", kind="percent", value=D("10"))
    q = quote_single("100.00", coupon)
    # subtotal = 100.00 * 1 = 100.00
    # discount = 100.00 * 10% = 10.00
    # goods = 90.00 -> >= 50.00 so standard shipping is free: 0.00
    # tax = 21% * (90.00 + 0.00) = 18.90
    # total = 100.00 - 10.00 + 0.00 + 18.90 = 108.90
    assert q.subtotal == D("100.00")
    assert q.discount == D("10.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")
    assert q.applied == ("coupon:SAVE10",)


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_25_takes_25_percent_off_subtotal():
    coupon = Coupon(code="Q", kind="percent", value=D("25"))
    q = quote_single("80.00", coupon)
    # subtotal = 80.00
    # discount = 80.00 * 25% = 20.00
    assert q.subtotal == D("80.00")
    assert q.discount == D("20.00")


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_scales_with_multiple_units():
    coupon = Coupon(code="SAVE10", kind="percent", value=D("10"))
    q = quote_single("12.50", coupon, qty=4)
    # subtotal = 12.50 * 4 = 50.00 (4 units: no volume discount)
    # discount = 50.00 * 10% = 5.00
    assert q.subtotal == D("50.00")
    assert q.discount == D("5.00")


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_discount_rounded_half_up_to_cent():
    coupon = Coupon(code="R", kind="percent", value=D("15"))
    q = quote_single("33.33", coupon)
    # subtotal = 33.33
    # discount = 33.33 * 15% = 4.9995 -> half up to the cent = 5.00
    assert q.subtotal == D("33.33")
    assert q.discount == D("5.00")


# ---------------------------------------------------------------- S3-AC2

@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_takes_value_in_euros_off():
    coupon = Coupon(code="FIX15", kind="fixed", value=D("15"))
    q = quote_single("100.00", coupon)
    # subtotal = 100.00
    # discount = 15.00 (fixed)
    # goods = 85.00 -> shipping free: 0.00
    # tax = 21% * 85.00 = 17.85
    # total = 100.00 - 15.00 + 0.00 + 17.85 = 102.85
    assert q.subtotal == D("100.00")
    assert q.discount == D("15.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("17.85")
    assert q.total == D("102.85")
    assert q.applied == ("coupon:FIX15",)


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_with_cents_value():
    coupon = Coupon(code="FIXC", kind="fixed", value=D("2.50"))
    q = quote_single("20.00", coupon)
    # subtotal = 20.00; discount = 2.50
    assert q.subtotal == D("20.00")
    assert q.discount == D("2.50")


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_larger_than_goods_is_capped_at_goods():
    coupon = Coupon(code="BIG", kind="fixed", value=D("25"))
    q = quote_single("10.00", coupon)
    # subtotal = 10.00
    # discount = min(25.00, 10.00) = 10.00 -> goods = 0.00
    # shipping: goods 0.00 < 50.00 -> 4.99
    # tax = 21% * (0.00 + 4.99) = 1.0479 -> 1.05
    # total = 10.00 - 10.00 + 4.99 + 1.05 = 6.04
    assert q.subtotal == D("10.00")
    assert q.discount == D("10.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("1.05")
    assert q.total == D("6.04")


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_equal_to_goods_brings_goods_to_zero():
    coupon = Coupon(code="EQ", kind="fixed", value=D("10.00"))
    q = quote_single("10.00", coupon)
    # subtotal = 10.00; discount = 10.00; goods = 0.00
    # shipping 4.99; tax = 21% * 4.99 = 1.0479 -> 1.05
    # total = 10.00 - 10.00 + 4.99 + 1.05 = 6.04
    assert q.discount == D("10.00")
    assert q.total == D("6.04")


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_one_cent_below_goods_leaves_one_cent():
    coupon = Coupon(code="ALMOST", kind="fixed", value=D("9.99"))
    q = quote_single("10.00", coupon)
    # subtotal = 10.00; discount = 9.99; goods = 0.01
    # shipping: 0.01 < 50.00 -> 4.99
    # tax = 21% * (0.01 + 4.99) = 21% * 5.00 = 1.05
    # total = 10.00 - 9.99 + 4.99 + 1.05 = 6.05
    assert q.discount == D("9.99")
    assert q.shipping == D("4.99")
    assert q.tax == D("1.05")
    assert q.total == D("6.05")


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_is_taken_after_loyalty_percentage_discount():
    coupon = Coupon(code="FIX10", kind="fixed", value=D("10"))
    q = quote_single("100.00", coupon, customer=Customer(tier="gold"))
    # subtotal = 100.00
    # loyalty = 100.00 * 5% = 5.00 ; goods after it = 95.00
    # fixed = 10.00 -> discount total = 5.00 + 10.00 = 15.00
    # goods = 85.00 -> shipping free; tax = 21% * 85.00 = 17.85
    # total = 100.00 - 15.00 + 0.00 + 17.85 = 102.85
    assert q.discount == D("15.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("17.85")
    assert q.total == D("102.85")
    assert q.applied == ("loyalty", "coupon:FIX10")


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_cap_applies_to_goods_after_loyalty_discount():
    coupon = Coupon(code="HUGE", kind="fixed", value=D("20"))
    q = quote_single("10.00", coupon, customer=Customer(tier="gold"))
    # subtotal = 10.00
    # loyalty = 10.00 * 5% = 0.50 ; goods after it = 9.50
    # fixed = min(20.00, 9.50) = 9.50 -> discount total = 0.50 + 9.50 = 10.00
    # goods = 0.00 -> shipping 4.99; tax = 21% * 4.99 = 1.0479 -> 1.05
    # total = 10.00 - 10.00 + 4.99 + 1.05 = 6.04
    assert q.discount == D("10.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("1.05")
    assert q.total == D("6.04")


# ---------------------------------------------------------------- S3-AC3

@pytest.mark.ac("S3-AC3")
def test_min_subtotal_not_met_by_one_cent_raises_coupon_error():
    coupon = Coupon(code="MIN50", kind="percent", value=D("10"), min_subtotal=D("50.00"))
    # subtotal = 49.99 < 50.00 -> CouponError
    with pytest.raises(CouponError):
        quote_single("49.99", coupon)


@pytest.mark.ac("S3-AC3")
def test_subtotal_equal_to_min_subtotal_is_enough():
    coupon = Coupon(code="MIN50", kind="percent", value=D("10"), min_subtotal=D("50.00"))
    q = quote_single("50.00", coupon)
    # subtotal = 50.00 == minimum -> valid
    # discount = 50.00 * 10% = 5.00
    assert q.subtotal == D("50.00")
    assert q.discount == D("5.00")
    assert q.applied == ("coupon:MIN50",)


@pytest.mark.ac("S3-AC3")
def test_subtotal_just_above_min_subtotal_is_accepted():
    coupon = Coupon(code="MIN50", kind="percent", value=D("10"), min_subtotal=D("50.00"))
    q = quote_single("50.01", coupon)
    # subtotal = 50.01 > 50.00 -> valid
    # discount = 50.01 * 10% = 5.001 -> 5.00
    assert q.subtotal == D("50.01")
    assert q.discount == D("5.00")


@pytest.mark.ac("S3-AC3")
def test_min_subtotal_applies_to_fixed_coupons_too():
    coupon = Coupon(code="FMIN", kind="fixed", value=D("5"), min_subtotal=D("30.00"))
    # subtotal = 29.99 < 30.00 -> CouponError
    with pytest.raises(CouponError):
        quote_single("29.99", coupon)
    q = quote_single("30.00", coupon)
    # subtotal = 30.00 == minimum -> valid, discount = 5.00
    assert q.discount == D("5.00")


@pytest.mark.ac("S3-AC3")
def test_min_subtotal_is_compared_with_subtotal_after_volume_discount():
    # 10 units * 10.00 = 100.00, volume 10% off -> subtotal 90.00
    below = Coupon(code="M95", kind="percent", value=D("10"), min_subtotal=D("95.00"))
    with pytest.raises(CouponError):
        quote_single("10.00", below, qty=10)
    exact = Coupon(code="M90", kind="percent", value=D("10"), min_subtotal=D("90.00"))
    q = quote_single("10.00", exact, qty=10)
    # subtotal = 90.00 == minimum -> valid
    # discount = 90.00 * 10% = 9.00
    assert q.subtotal == D("90.00")
    assert q.discount == D("9.00")


@pytest.mark.ac("S3-AC3")
def test_zero_min_subtotal_never_blocks_coupon():
    coupon = Coupon(code="ANY", kind="fixed", value=D("1"))
    q = quote_single("1.00", coupon)
    # subtotal = 1.00; discount = 1.00 (capped at goods, equal)
    assert q.discount == D("1.00")


# ---------------------------------------------------------------- S3-AC4

@pytest.mark.ac("S3-AC4")
def test_coupon_expired_yesterday_raises_coupon_error():
    coupon = Coupon(code="OLD", kind="percent", value=D("10"), expires=date(2025, 6, 14))
    with pytest.raises(CouponError):
        quote_single("100.00", coupon, today=date(2025, 6, 15))


@pytest.mark.ac("S3-AC4")
def test_coupon_still_valid_on_its_expiry_date():
    coupon = Coupon(code="LAST", kind="percent", value=D("10"), expires=date(2025, 6, 15))
    q = quote_single("100.00", coupon, today=date(2025, 6, 15))
    # subtotal = 100.00; discount = 10.00
    assert q.discount == D("10.00")
    assert q.applied == ("coupon:LAST",)


@pytest.mark.ac("S3-AC4")
def test_coupon_valid_the_day_before_its_expiry_date():
    coupon = Coupon(code="SOON", kind="percent", value=D("10"), expires=date(2025, 6, 16))
    q = quote_single("100.00", coupon, today=date(2025, 6, 15))
    # subtotal = 100.00; discount = 10.00
    assert q.discount == D("10.00")


@pytest.mark.ac("S3-AC4")
def test_coupon_expired_across_year_boundary_raises():
    coupon = Coupon(code="NYE", kind="fixed", value=D("5"), expires=date(2025, 12, 31))
    with pytest.raises(CouponError):
        quote_single("100.00", coupon, today=date(2026, 1, 1))


@pytest.mark.ac("S3-AC4")
def test_fixed_coupon_valid_on_expiry_date():
    coupon = Coupon(code="FLAST", kind="fixed", value=D("5"), expires=date(2025, 12, 31))
    q = quote_single("100.00", coupon, today=date(2025, 12, 31))
    # subtotal = 100.00; discount = 5.00
    assert q.discount == D("5.00")


@pytest.mark.ac("S3-AC4")
def test_coupon_without_expiry_date_never_expires():
    coupon = Coupon(code="FOREVER", kind="percent", value=D("10"), expires=None)
    q = quote_single("100.00", coupon, today=date(2099, 12, 31))
    # subtotal = 100.00; discount = 10.00
    assert q.discount == D("10.00")


# ---------------------------------------------------------------- S3-AC5

@pytest.mark.ac("S3-AC5")
@pytest.mark.parametrize("kind", ["bogus", "free_shipping", ""])
def test_unknown_coupon_kind_raises_coupon_error(kind):
    coupon = Coupon(code="WEIRD", kind=kind, value=D("10"))
    with pytest.raises(CouponError):
        quote_single("100.00", coupon)


@pytest.mark.ac("S3-AC5")
def test_coupon_error_is_a_cart_error():
    assert issubclass(CouponError, CartError)
    coupon = Coupon(code="WEIRD", kind="bogus", value=D("10"))
    with pytest.raises(CartError):
        quote_single("100.00", coupon)
