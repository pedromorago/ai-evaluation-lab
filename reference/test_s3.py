from datetime import date, timedelta
from decimal import Decimal as D

import pytest

from checkout import CartError, Coupon, CouponError, Customer, Line, Product, price_cart

TODAY = date(2026, 5, 1)
CATALOG = {
    "MUG": Product("MUG", "Mug", D("8.00")),
    "PEN": Product("PEN", "Pen", D("1.25")),
    "LAMP": Product("LAMP", "Lamp", D("45.00")),
}


def quote(*lines, **kw):
    return price_cart([Line(sku, qty) for sku, qty in lines], CATALOG, today=TODAY, **kw)


def percent(value, **kw):
    return Coupon("SAVE", "percent", D(value), **kw)


def fixed(value, **kw):
    return Coupon("OFF", "fixed", D(value), **kw)


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_takes_a_percentage_off_the_subtotal():
    q = quote(("LAMP", 2), coupon=percent("10"))
    assert (q.subtotal, q.discount, q.applied) == (D("90.00"), D("9.00"), ("coupon:SAVE",))


@pytest.mark.ac("S3-AC1", "S6-AC2")
def test_percent_discount_is_rounded_before_the_total():
    q = quote(("MUG", 2), ("PEN", 3), coupon=percent("10"))
    assert (q.discount, q.shipping, q.tax, q.total) == (D("1.98"), D("4.99"), D("4.78"), D("27.54"))


@pytest.mark.ac("S3-AC1")
def test_a_small_percent_discount_still_applies():
    q = quote(("PEN", 3), coupon=percent("10"))
    assert q.discount == D("0.38")


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_takes_euros_off():
    q = quote(("MUG", 2), ("PEN", 3), coupon=fixed("5"))
    assert (q.discount, q.applied) == (D("5.00"), ("coupon:OFF",))


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_never_takes_the_goods_below_zero():
    q = quote(("MUG", 2), ("PEN", 3), coupon=fixed("100"))
    assert (q.discount, q.shipping, q.tax, q.total) == (D("19.75"), D("4.99"), D("1.05"), D("6.04"))


@pytest.mark.ac("S3-AC2", "S4-AC2")
def test_fixed_coupon_is_capped_after_the_loyalty_discount():
    q = quote(("MUG", 2), ("PEN", 3), customer=Customer("gold"), coupon=fixed("100"))
    assert q.discount == D("19.75")
    assert q.total == D("6.04")


@pytest.mark.ac("S3-AC3")
def test_subtotal_below_the_minimum_is_rejected():
    with pytest.raises(CouponError):
        quote(("LAMP", 1), coupon=percent("10", min_subtotal=D("45.01")))


@pytest.mark.ac("S3-AC3")
def test_subtotal_equal_to_the_minimum_is_enough():
    assert quote(("LAMP", 1), coupon=percent("10", min_subtotal=D("45.00"))).discount == D("4.50")


@pytest.mark.ac("S3-AC3", "S6-AC2")
def test_minimum_is_checked_against_the_rounded_subtotal():
    # 50 pens at 15% off: 53.125, which the quote rounds to 53.13
    q = quote(("PEN", 50), coupon=fixed("1", min_subtotal=D("53.13")))
    assert q.discount == D("1.00")


@pytest.mark.ac("S3-AC4")
def test_coupon_is_valid_on_its_expiry_date():
    assert quote(("LAMP", 1), coupon=percent("10", expires=TODAY)).discount == D("4.50")


@pytest.mark.ac("S3-AC4")
def test_coupon_is_rejected_after_its_expiry_date():
    with pytest.raises(CouponError):
        quote(("LAMP", 1), coupon=percent("10", expires=TODAY - timedelta(days=1)))


@pytest.mark.ac("S3-AC4")
def test_coupon_without_expiry_never_expires():
    assert quote(("LAMP", 1), coupon=percent("10")).discount == D("4.50")


@pytest.mark.ac("S3-AC5")
def test_unknown_coupon_kind_is_rejected():
    with pytest.raises(CouponError):
        quote(("LAMP", 1), coupon=Coupon("ODD", "bogo", D("1")))


@pytest.mark.ac("S3-AC5")
def test_coupon_error_is_a_cart_error():
    assert issubclass(CouponError, CartError)
