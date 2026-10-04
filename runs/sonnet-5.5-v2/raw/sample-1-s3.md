```python
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

TODAY = date(2026, 1, 15)
D = Decimal


def quote(qty, unit_price, coupon=None, customer=None, category="general", today=TODAY):
    catalog = {"A": Product("A", "Item A", D(unit_price), category)}
    kwargs = {"today": today, "coupon": coupon}
    if customer is not None:
        kwargs["customer"] = customer
    return price_cart([Line("A", qty)], catalog, **kwargs)


# ---------------------------------------------------------------- S3-AC1

@pytest.mark.ac("S3-AC1")
def test_percent_coupon_10_takes_ten_percent_off_subtotal():
    coupon = Coupon("SAVE10", "percent", D("10"))
    q = quote(1, "100.00", coupon)
    # subtotal = 100.00
    # discount = 10% of 100.00 = 10.00
    # goods = 90.00 -> shipping free (>= 50.00) -> 0.00
    # tax = 21% of (90.00 + 0.00) = 18.90
    # total = 100.00 - 10.00 + 0.00 + 18.90 = 108.90
    assert q.subtotal == D("100.00")
    assert q.discount == D("10.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")
    assert q.applied == ("coupon:SAVE10",)


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_25_takes_a_quarter_off_subtotal():
    coupon = Coupon("Q25", "percent", D("25"))
    q = quote(1, "80.00", coupon)
    # subtotal = 80.00
    # discount = 25% of 80.00 = 20.00
    # goods = 60.00 -> shipping free
    # tax = 21% of 60.00 = 12.60
    # total = 80.00 - 20.00 + 0.00 + 12.60 = 72.60
    assert q.discount == D("20.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("12.60")
    assert q.total == D("72.60")


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_discount_is_rounded_to_the_cent():
    coupon = Coupon("SAVE10", "percent", D("10"))
    q = quote(1, "33.33", coupon)
    # subtotal = 33.33
    # discount = 10% of 33.33 = 3.333 -> 3.33
    # goods = 33.33 - 3.33 = 30.00 -> below 50.00, shipping 4.99
    # tax = 21% of (30.00 + 4.99) = 21% of 34.99 = 7.3479 -> 7.35
    # total = 33.33 - 3.33 + 4.99 + 7.35 = 42.34
    assert q.subtotal == D("33.33")
    assert q.discount == D("3.33")
    assert q.shipping == D("4.99")
    assert q.tax == D("7.35")
    assert q.total == D("42.34")


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_discount_rounds_half_up():
    coupon = Coupon("SAVE10", "percent", D("10"))
    q = quote(1, "0.05", coupon)
    # subtotal = 0.05
    # discount = 10% of 0.05 = 0.005 -> half up -> 0.01
    # goods = 0.04 -> shipping 4.99
    # tax = 21% of (0.04 + 4.99) = 21% of 5.03 = 1.0563 -> 1.06
    # total = 0.05 - 0.01 + 4.99 + 1.06 = 6.09
    assert q.discount == D("0.01")
    assert q.shipping == D("4.99")
    assert q.tax == D("1.06")
    assert q.total == D("6.09")


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_applies_to_subtotal_after_volume_discount():
    coupon = Coupon("C20", "percent", D("20"))
    q = quote(10, "10.00", coupon)
    # line = 10 * 10.00 = 100.00, volume 10% off -> subtotal = 90.00
    # coupon discount = 20% of 90.00 = 18.00
    # goods = 72.00 -> shipping free
    # tax = 21% of 72.00 = 15.12
    # total = 90.00 - 18.00 + 0.00 + 15.12 = 87.12
    assert q.subtotal == D("90.00")
    assert q.discount == D("18.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("15.12")
    assert q.total == D("87.12")
    assert q.applied == ("volume:A", "coupon:C20")


# ---------------------------------------------------------------- S3-AC2

@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_takes_value_in_euros_off():
    coupon = Coupon("F10", "fixed", D("10"))
    q = quote(1, "100.00", coupon)
    # subtotal = 100.00
    # discount = 10.00
    # goods = 90.00 -> shipping free
    # tax = 21% of 90.00 = 18.90
    # total = 100.00 - 10.00 + 0.00 + 18.90 = 108.90
    assert q.subtotal == D("100.00")
    assert q.discount == D("10.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")
    assert q.applied == ("coupon:F10",)


@pytest.mark.ac("S3-AC2")
@pytest.mark.parametrize("value", ["15.00", "15.01", "20.00", "100.00"])
def test_fixed_coupon_equal_to_or_above_goods_never_goes_below_zero(value):
    coupon = Coupon("BIG", "fixed", D(value))
    q = quote(1, "15.00", coupon)
    # subtotal = 15.00
    # discount = min(value, 15.00) = 15.00 (goods cannot go below 0.00)
    # goods = 0.00 -> below 50.00, shipping 4.99
    # tax = 21% of (0.00 + 4.99) = 1.0479 -> 1.05
    # total = 15.00 - 15.00 + 4.99 + 1.05 = 5.04
    assert q.subtotal == D("15.00")
    assert q.discount == D("15.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("1.05")
    assert q.total == D("5.04")


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_just_below_goods_is_taken_in_full():
    coupon = Coupon("F", "fixed", D("14.99"))
    q = quote(1, "15.00", coupon)
    # subtotal = 15.00
    # discount = 14.99
    # goods = 0.01 -> shipping 4.99
    # tax = 21% of (0.01 + 4.99) = 21% of 5.00 = 1.05
    # total = 15.00 - 14.99 + 4.99 + 1.05 = 6.05
    assert q.discount == D("14.99")
    assert q.shipping == D("4.99")
    assert q.tax == D("1.05")
    assert q.total == D("6.05")


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_is_taken_off_after_loyalty_percentage_discount():
    coupon = Coupon("F10", "fixed", D("10"))
    q = quote(1, "100.00", coupon, customer=Customer(tier="gold"))
    # subtotal = 100.00
    # loyalty = 5% of 100.00 = 5.00
    # fixed = 10.00 (goods still 95.00, enough)
    # discount = 5.00 + 10.00 = 15.00
    # goods = 85.00 -> shipping free
    # tax = 21% of 85.00 = 17.85
    # total = 100.00 - 15.00 + 0.00 + 17.85 = 102.85
    assert q.discount == D("15.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("17.85")
    assert q.total == D("102.85")
    assert q.applied == ("loyalty", "coupon:F10")


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_is_capped_by_what_remains_after_percentage_discount():
    coupon = Coupon("F25", "fixed", D("25"))
    q = quote(1, "20.00", coupon, customer=Customer(tier="gold"))
    # subtotal = 20.00
    # loyalty = 5% of 20.00 = 1.00 -> 19.00 remains
    # fixed = min(25.00, 19.00) = 19.00
    # discount = 1.00 + 19.00 = 20.00
    # goods = 0.00 -> shipping 4.99
    # tax = 21% of 4.99 = 1.0479 -> 1.05
    # total = 20.00 - 20.00 + 4.99 + 1.05 = 5.04
    assert q.discount == D("20.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("1.05")
    assert q.total == D("5.04")


# ---------------------------------------------------------------- S3-AC3

@pytest.mark.ac("S3-AC3")
def test_min_subtotal_not_reached_raises_coupon_error():
    coupon = Coupon("MIN50", "percent", D("10"), min_subtotal=D("50.00"))
    # subtotal = 49.99 < 50.00
    with pytest.raises(CouponError):
        quote(1, "49.99", coupon)


@pytest.mark.ac("S3-AC3")
def test_min_subtotal_not_reached_fixed_coupon_raises_coupon_error():
    coupon = Coupon("MIN50", "fixed", D("5"), min_subtotal=D("50.00"))
    # subtotal = 49.99 < 50.00
    with pytest.raises(CouponError):
        quote(1, "49.99", coupon)


@pytest.mark.ac("S3-AC3")
def test_subtotal_equal_to_min_subtotal_is_enough():
    coupon = Coupon("MIN50", "percent", D("10"), min_subtotal=D("50.00"))
    q = quote(1, "50.00", coupon)
    # subtotal = 50.00
    # discount = 10% of 50.00 = 5.00
    # goods = 45.00 -> below 50.00, shipping 4.99
    # tax = 21% of (45.00 + 4.99) = 21% of 49.99 = 10.4979 -> 10.50
    # total = 50.00 - 5.00 + 4.99 + 10.50 = 60.49
    assert q.subtotal == D("50.00")
    assert q.discount == D("5.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("10.50")
    assert q.total == D("60.49")
    assert q.applied == ("coupon:MIN50",)


@pytest.mark.ac("S3-AC3")
def test_subtotal_above_min_subtotal_is_accepted():
    coupon = Coupon("MIN50", "percent", D("10"), min_subtotal=D("50.00"))
    q = quote(1, "50.01", coupon)
    # subtotal = 50.01
    # discount = 10% of 50.01 = 5.001 -> 5.00
    # goods = 45.01 -> shipping 4.99
    # tax = 21% of (45.01 + 4.99) = 21% of 50.00 = 10.50
    # total = 50.01 - 5.00 + 4.99 + 10.50 = 60.50
    assert q.subtotal == D("50.01")
    assert q.discount == D("5.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("10.50")
    assert q.total == D("60.50")


@pytest.mark.ac("S3-AC3")
def test_min_subtotal_is_checked_against_subtotal_after_volume_discount():
    # 10 units * 6.00 = 60.00, volume 10% off -> subtotal 54.00
    too_high = Coupon("MIN55", "percent", D("10"), min_subtotal=D("55.00"))
    with pytest.raises(CouponError):
        quote(10, "6.00", too_high)


@pytest.mark.ac("S3-AC3")
def test_min_subtotal_equal_to_subtotal_after_volume_discount_is_enough():
    coupon = Coupon("MIN54", "percent", D("10"), min_subtotal=D("54.00"))
    q = quote(10, "6.00", coupon)
    # line = 10 * 6.00 = 60.00, volume 10% off -> subtotal = 54.00 (== minimum)
    # discount = 10% of 54.00 = 5.40
    # goods = 48.60 -> below 50.00, shipping 4.99
    # tax = 21% of (48.60 + 4.99) = 21% of 53.59 = 11.2539 -> 11.25
    # total = 54.00 - 5.40 + 4.99 + 11.25 = 64.84
    assert q.subtotal == D("54.00")
    assert q.discount == D("5.40")
    assert q.shipping == D("4.99")
    assert q.tax == D("11.25")
    assert q.total == D("64.84")


# ---------------------------------------------------------------- S3-AC4

@pytest.mark.ac("S3-AC4")
def test_coupon_expired_yesterday_raises_coupon_error():
    coupon = Coupon("OLD", "percent", D("10"), expires=TODAY - timedelta(days=1))
    with pytest.raises(CouponError):
        quote(1, "100.00", coupon)


@pytest.mark.ac("S3-AC4")
def test_expired_fixed_coupon_raises_coupon_error():
    coupon = Coupon("OLDF", "fixed", D("5"), expires=TODAY - timedelta(days=1))
    with pytest.raises(CouponError):
        quote(1, "100.00", coupon)


@pytest.mark.ac("S3-AC4")
def test_coupon_expiry_across_month_boundary_raises_coupon_error():
    coupon = Coupon("OLD", "percent", D("10"), expires=date(2026, 2, 28))
    with pytest.raises(CouponError):
        quote(1, "100.00", coupon, today=date(2026, 3, 1))


@pytest.mark.ac("S3-AC4")
def test_coupon_is_still_valid_on_its_expiry_date():
    coupon = Coupon("LAST", "percent", D("10"), expires=TODAY)
    q = quote(1, "100.00", coupon)
    # subtotal = 100.00
    # discount = 10% of 100.00 = 10.00
    # goods = 90.00 -> shipping free
    # tax = 21% of 90.00 = 18.90
    # total = 100.00 - 10.00 + 0.00 + 18.90 = 108.90
    assert q.discount == D("10.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")
    assert q.applied == ("coupon:LAST",)


@pytest.mark.ac("S3-AC4")
def test_coupon_is_valid_the_day_before_its_expiry_date():
    coupon = Coupon("SOON", "percent", D("10"), expires=TODAY + timedelta(days=1))
    q = quote(1, "100.00", coupon)
    # same amounts as a 10% coupon on 100.00: discount 10.00, tax 18.90, total 108.90
    assert q.discount == D("10.00")
    assert q.total == D("108.90")


@pytest.mark.ac("S3-AC4")
def test_coupon_without_expiry_date_never_expires():
    coupon = Coupon("FOREVER", "percent", D("10"), expires=None)
    q = quote(1, "100.00", coupon, today=date(2099, 12, 31))
    # subtotal = 100.00, discount = 10.00, goods = 90.00 -> shipping free
    # tax = 21% of 90.00 = 18.90
    # total = 100.00 - 10.00 + 0.00 + 18.90 = 108.90
    assert q.discount == D("10.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")
    assert q.applied == ("coupon:FOREVER",)


# ---------------------------------------------------------------- S3-AC5

@pytest.mark.ac("S3-AC5")
@pytest.mark.parametrize("kind", ["bogus", "free_shipping", ""])
def test_unknown_coupon_kind_raises_coupon_error(kind):
    coupon = Coupon("WEIRD", kind, D("10"))
    with pytest.raises(CouponError):
        quote(1, "100.00", coupon)


@pytest.mark.ac("S3-AC5")
def test_coupon_error_is_a_cart_error():
    assert issubclass(CouponError, CartError)
    coupon = Coupon("WEIRD", "bogus", D("10"))
    with pytest.raises(CartError):
        quote(1, "100.00", coupon)
```