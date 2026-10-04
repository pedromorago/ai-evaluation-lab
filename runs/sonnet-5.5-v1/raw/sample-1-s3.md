```python
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
D = Decimal


def catalog(price="100.00", sku="G-1", category="general"):
    return {sku: Product(sku=sku, name="Item", unit_price=D(price), category=category)}


def price(coupon, unit_price="100.00", qty=1, **kwargs):
    return price_cart(
        [Line("G-1", qty)],
        catalog(unit_price),
        today=TODAY,
        coupon=coupon,
        **kwargs,
    )


# ---------------------------------------------------------------- S3-AC1


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_takes_percentage_off_subtotal():
    q = price(Coupon("SAVE10", "percent", D("10")))
    assert q.subtotal == D("100.00")
    assert q.discount == D("10.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")
    assert q.applied == ("coupon:SAVE10",)


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_value_is_a_percentage_not_a_fraction():
    q = price(Coupon("HALF", "percent", D("50")))
    assert q.discount == D("50.00")


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_discount_rounds_half_up():
    # 33.33 * 15% = 4.9995 -> 5.00
    q = price(Coupon("P15", "percent", D("15")), unit_price="33.33")
    assert q.subtotal == D("33.33")
    assert q.discount == D("5.00")


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_applies_to_subtotal_after_volume_discount():
    # 10 x 10.00 = 100 -> 90.00 after volume discount; 10% of 90 = 9.00
    q = price(Coupon("SAVE10", "percent", D("10")), unit_price="10.00", qty=10)
    assert q.subtotal == D("90.00")
    assert q.discount == D("9.00")


# ---------------------------------------------------------------- S3-AC2


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_takes_euros_off():
    q = price(Coupon("FIVE", "fixed", D("5")))
    assert q.subtotal == D("100.00")
    assert q.discount == D("5.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("19.95")
    assert q.total == D("114.95")
    assert q.applied == ("coupon:FIVE",)


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_is_taken_off_after_percentage_discount():
    # Gold 5% loyalty = 5.00 then fixed 10 -> total discount 15.00
    q = price(Coupon("TEN", "fixed", D("10")), customer=Customer(tier="gold"))
    assert q.discount == D("15.00")


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_never_takes_goods_below_zero():
    q = price(Coupon("BIG", "fixed", D("25")), unit_price="10.00")
    assert q.subtotal == D("10.00")
    assert q.discount == D("10.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("1.05")
    assert q.total == D("6.04")


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_equal_to_goods_gives_zero_goods():
    q = price(Coupon("EXACT", "fixed", D("10")), unit_price="10.00")
    assert q.discount == D("10.00")
    assert q.total == q.shipping + q.tax


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_is_capped_by_what_remains_after_percentage_discount():
    # Gold on 20.00: loyalty 1.00 -> 19.00 left; fixed 50 can only take 19.00
    q = price(
        Coupon("HUGE", "fixed", D("50")),
        unit_price="20.00",
        customer=Customer(tier="gold"),
    )
    assert q.discount == D("20.00")
    assert q.applied == ("loyalty", "coupon:HUGE")


# ---------------------------------------------------------------- S3-AC3


@pytest.mark.ac("S3-AC3")
def test_subtotal_below_minimum_raises_coupon_error():
    coupon = Coupon("MIN50", "percent", D("10"), min_subtotal=D("50.00"))
    with pytest.raises(CouponError):
        price(coupon, unit_price="49.99")


@pytest.mark.ac("S3-AC3")
def test_subtotal_equal_to_minimum_is_enough():
    coupon = Coupon("MIN50", "percent", D("10"), min_subtotal=D("50.00"))
    q = price(coupon, unit_price="50.00")
    assert q.discount == D("5.00")
    assert q.applied == ("coupon:MIN50",)


@pytest.mark.ac("S3-AC3")
def test_subtotal_above_minimum_is_accepted():
    coupon = Coupon("MIN50", "fixed", D("5"), min_subtotal=D("50.00"))
    q = price(coupon, unit_price="50.01")
    assert q.discount == D("5.00")


@pytest.mark.ac("S3-AC3")
def test_minimum_applies_to_fixed_coupons_too():
    coupon = Coupon("MIN50", "fixed", D("5"), min_subtotal=D("50.00"))
    with pytest.raises(CouponError):
        price(coupon, unit_price="49.99")


@pytest.mark.ac("S3-AC3")
def test_minimum_is_checked_against_subtotal_after_volume_discount():
    # 10 x 10.00 = 100.00 raw, 90.00 after the 10% volume discount
    coupon = Coupon("MIN95", "percent", D("10"), min_subtotal=D("95.00"))
    with pytest.raises(CouponError):
        price(coupon, unit_price="10.00", qty=10)


@pytest.mark.ac("S3-AC3")
def test_default_minimum_imposes_no_restriction():
    q = price(Coupon("ANY", "fixed", D("1")), unit_price="2.00")
    assert q.discount == D("1.00")


# ---------------------------------------------------------------- S3-AC4


@pytest.mark.ac("S3-AC4")
def test_coupon_expired_yesterday_raises():
    coupon = Coupon("OLD", "percent", D("10"), expires=date(2025, 6, 14))
    with pytest.raises(CouponError):
        price(coupon)


@pytest.mark.ac("S3-AC4")
def test_coupon_is_valid_on_its_expiry_date():
    coupon = Coupon("LAST", "percent", D("10"), expires=TODAY)
    q = price(coupon)
    assert q.discount == D("10.00")
    assert q.applied == ("coupon:LAST",)


@pytest.mark.ac("S3-AC4")
def test_coupon_before_expiry_is_valid():
    coupon = Coupon("SOON", "percent", D("10"), expires=date(2025, 6, 16))
    assert price(coupon).discount == D("10.00")


@pytest.mark.ac("S3-AC4")
def test_coupon_without_expiry_never_expires():
    coupon = Coupon("FOREVER", "percent", D("10"))
    q = price_cart(
        [Line("G-1", 1)], catalog(), today=date(2099, 12, 31), coupon=coupon
    )
    assert q.discount == D("10.00")


@pytest.mark.ac("S3-AC4")
def test_expiry_is_judged_against_the_today_argument():
    coupon = Coupon("JUNE", "percent", D("10"), expires=date(2025, 6, 30))
    ok = price_cart([Line("G-1", 1)], catalog(), today=date(2025, 6, 30), coupon=coupon)
    assert ok.discount == D("10.00")
    with pytest.raises(CouponError):
        price_cart([Line("G-1", 1)], catalog(), today=date(2025, 7, 1), coupon=coupon)


@pytest.mark.ac("S3-AC4")
def test_expired_fixed_coupon_raises():
    coupon = Coupon("OLDFIX", "fixed", D("5"), expires=date(2024, 1, 1))
    with pytest.raises(CouponError):
        price(coupon)


# ---------------------------------------------------------------- S3-AC5


@pytest.mark.ac("S3-AC5")
def test_unknown_kind_raises_coupon_error():
    with pytest.raises(CouponError):
        price(Coupon("WEIRD", "bogus", D("10")))


@pytest.mark.ac("S3-AC5")
def test_empty_kind_raises_coupon_error():
    with pytest.raises(CouponError):
        price(Coupon("BLANK", "", D("10")))


@pytest.mark.ac("S3-AC5")
def test_unknown_kind_raises_even_if_otherwise_valid():
    coupon = Coupon(
        "BOGO", "bogo", D("1"), min_subtotal=D("0"), expires=date(2099, 1, 1)
    )
    with pytest.raises(CouponError):
        price(coupon)


# ------------------------------------------------- error hierarchy (all ACs)


@pytest.mark.ac("S3-AC3", "S3-AC4", "S3-AC5")
def test_coupon_error_is_a_cart_error():
    assert issubclass(CouponError, CartError)
    with pytest.raises(CartError):
        price(Coupon("WEIRD", "bogus", D("10")))
    with pytest.raises(CartError):
        price(Coupon("OLD", "percent", D("10"), expires=date(2025, 6, 14)))
    with pytest.raises(CartError):
        price(Coupon("MIN", "percent", D("10"), min_subtotal=D("500")))
```