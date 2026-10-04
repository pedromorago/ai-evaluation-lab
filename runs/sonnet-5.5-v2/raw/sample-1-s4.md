```python
from datetime import date
from decimal import Decimal

import pytest

from checkout import (
    Coupon,
    Customer,
    Line,
    Product,
    price_cart,
)

TODAY = date(2026, 1, 15)
D = Decimal


def catalog_with(price, sku="A"):
    return {sku: Product(sku=sku, name="Item", unit_price=D(price))}


def quote(price, customer=None, coupon=None, quantity=1, shipping="standard"):
    return price_cart(
        [Line("A", quantity)],
        catalog_with(price),
        today=TODAY,
        customer=customer if customer is not None else Customer(),
        coupon=coupon,
        shipping=shipping,
    )


def pct(code, value):
    return Coupon(code=code, kind="percent", value=D(value))


def fixed(code, value):
    return Coupon(code=code, kind="fixed", value=D(value))


GOLD = Customer(tier="gold")
STANDARD = Customer(tier="standard")


@pytest.mark.ac("S4-AC1")
def test_gold_customer_gets_five_percent_off_subtotal():
    q = quote("100.00", customer=GOLD)
    # subtotal = 100.00
    # loyalty = 5% of 100.00 = 5.00
    # goods = 95.00 (>= 50.00 so standard shipping is free) -> shipping 0.00
    # tax = 21% of (95.00 + 0.00) = 19.95
    # total = 100.00 - 5.00 + 0.00 + 19.95 = 114.95
    assert q.subtotal == D("100.00")
    assert q.discount == D("5.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("19.95")
    assert q.total == D("114.95")
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S4-AC1")
def test_standard_customer_gets_no_loyalty_discount():
    q = quote("100.00", customer=STANDARD)
    # subtotal = 100.00, no discount, goods = 100.00 -> free shipping
    # tax = 21% of 100.00 = 21.00
    # total = 100.00 - 0.00 + 0.00 + 21.00 = 121.00
    assert q.subtotal == D("100.00")
    assert q.discount == D("0.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("21.00")
    assert q.total == D("121.00")
    assert q.applied == ()


@pytest.mark.ac("S4-AC1")
def test_default_customer_is_standard_and_gets_no_loyalty_discount():
    q = price_cart([Line("A", 1)], catalog_with("100.00"), today=TODAY)
    # default customer is standard -> no discount; total = 100.00 + 21.00 = 121.00
    assert q.discount == D("0.00")
    assert q.total == D("121.00")
    assert q.applied == ()


@pytest.mark.ac("S4-AC1", "S6-AC2")
def test_gold_loyalty_discount_rounds_half_up_to_the_cent():
    q = quote("10.10", customer=GOLD)
    # subtotal = 10.10
    # loyalty = 5% of 10.10 = 0.505 -> half up -> 0.51
    # goods = 10.10 - 0.51 = 9.59 (< 50.00) -> shipping 4.99
    # tax = 21% of (9.59 + 4.99) = 21% of 14.58 = 3.0618 -> 3.06
    # total = 10.10 - 0.51 + 4.99 + 3.06 = 17.64
    assert q.subtotal == D("10.10")
    assert q.discount == D("0.51")
    assert q.shipping == D("4.99")
    assert q.tax == D("3.06")
    assert q.total == D("17.64")


@pytest.mark.ac("S4-AC1", "S5-AC1")
def test_gold_goods_exactly_50_after_loyalty_get_free_shipping():
    q = quote("52.63", customer=GOLD)
    # subtotal = 52.63
    # loyalty = 5% of 52.63 = 2.6315 -> 2.63
    # goods = 52.63 - 2.63 = 50.00 -> exactly 50.00, shipping free
    # tax = 21% of 50.00 = 10.50
    # total = 52.63 - 2.63 + 0.00 + 10.50 = 60.50
    assert q.discount == D("2.63")
    assert q.shipping == D("0.00")
    assert q.tax == D("10.50")
    assert q.total == D("60.50")


@pytest.mark.ac("S4-AC1", "S5-AC1")
def test_gold_goods_below_50_after_loyalty_pay_standard_shipping():
    q = quote("52.00", customer=GOLD)
    # subtotal = 52.00 (would qualify for free shipping before loyalty)
    # loyalty = 5% of 52.00 = 2.60
    # goods = 52.00 - 2.60 = 49.40 (< 50.00) -> shipping 4.99
    # tax = 21% of (49.40 + 4.99) = 21% of 54.39 = 11.4219 -> 11.42
    # total = 52.00 - 2.60 + 4.99 + 11.42 = 65.81
    assert q.discount == D("2.60")
    assert q.shipping == D("4.99")
    assert q.tax == D("11.42")
    assert q.total == D("65.81")


@pytest.mark.ac("S4-AC2")
def test_gold_with_larger_percent_coupon_applies_only_the_coupon():
    q = quote("100.00", customer=GOLD, coupon=pct("SAVE10", "10"))
    # subtotal = 100.00
    # loyalty = 5.00, coupon = 10% of 100.00 = 10.00 -> coupon is larger, only it applies
    # discount = 10.00, goods = 90.00 -> free shipping
    # tax = 21% of 90.00 = 18.90
    # total = 100.00 - 10.00 + 0.00 + 18.90 = 108.90
    assert q.discount == D("10.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")
    assert q.applied == ("coupon:SAVE10",)


@pytest.mark.ac("S4-AC2")
def test_gold_with_smaller_percent_coupon_applies_only_loyalty():
    q = quote("100.00", customer=GOLD, coupon=pct("SAVE3", "3"))
    # subtotal = 100.00
    # loyalty = 5.00, coupon = 3.00 -> loyalty is larger, only it applies
    # discount = 5.00, goods = 95.00 -> free shipping
    # tax = 21% of 95.00 = 19.95
    # total = 100.00 - 5.00 + 0.00 + 19.95 = 114.95
    assert q.discount == D("5.00")
    assert q.tax == D("19.95")
    assert q.total == D("114.95")
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S4-AC2")
def test_gold_with_equal_percent_coupon_applies_the_coupon_not_loyalty():
    q = quote("100.00", customer=GOLD, coupon=pct("FIVE", "5"))
    # subtotal = 100.00
    # loyalty = 5.00, coupon = 5% of 100.00 = 5.00 -> equal, the coupon wins
    # discount = 5.00 (not 10.00), goods = 95.00 -> free shipping
    # tax = 21% of 95.00 = 19.95
    # total = 100.00 - 5.00 + 0.00 + 19.95 = 114.95
    assert q.discount == D("5.00")
    assert q.tax == D("19.95")
    assert q.total == D("114.95")
    assert q.applied == ("coupon:FIVE",)


@pytest.mark.ac("S4-AC2")
def test_percent_coupon_just_below_loyalty_rate_loses_to_loyalty():
    q = quote("100.00", customer=GOLD, coupon=pct("LOW", "4.9"))
    # subtotal = 100.00
    # loyalty = 5.00, coupon = 4.9% of 100.00 = 4.90 -> loyalty is larger
    # discount = 5.00, goods = 95.00 -> free shipping
    # tax = 21% of 95.00 = 19.95
    # total = 100.00 - 5.00 + 19.95 = 114.95
    assert q.discount == D("5.00")
    assert q.total == D("114.95")
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S4-AC2")
def test_percent_coupon_just_above_loyalty_rate_beats_loyalty():
    q = quote("100.00", customer=GOLD, coupon=pct("HIGH", "5.1"))
    # subtotal = 100.00
    # loyalty = 5.00, coupon = 5.1% of 100.00 = 5.10 -> coupon is larger
    # discount = 5.10, goods = 94.90 -> free shipping
    # tax = 21% of 94.90 = 19.929 -> 19.93
    # total = 100.00 - 5.10 + 0.00 + 19.93 = 114.83
    assert q.discount == D("5.10")
    assert q.tax == D("19.93")
    assert q.total == D("114.83")
    assert q.applied == ("coupon:HIGH",)


@pytest.mark.ac("S4-AC2")
def test_standard_customer_with_percent_coupon_gets_the_coupon():
    q = quote("100.00", customer=STANDARD, coupon=pct("SAVE10", "10"))
    # subtotal = 100.00, no loyalty; coupon = 10.00
    # goods = 90.00 -> free shipping
    # tax = 21% of 90.00 = 18.90
    # total = 100.00 - 10.00 + 0.00 + 18.90 = 108.90
    assert q.discount == D("10.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")
    assert q.applied == ("coupon:SAVE10",)


@pytest.mark.ac("S4-AC2")
def test_fixed_coupon_stacks_with_loyalty_discount():
    q = quote("100.00", customer=GOLD, coupon=fixed("FIX10", "10"))
    # subtotal = 100.00
    # loyalty = 5.00 -> 95.00; then fixed coupon 10.00 -> 85.00
    # discount = 5.00 + 10.00 = 15.00, goods = 85.00 -> free shipping
    # tax = 21% of 85.00 = 17.85
    # total = 100.00 - 15.00 + 0.00 + 17.85 = 102.85
    assert q.discount == D("15.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("17.85")
    assert q.total == D("102.85")
    assert q.applied == ("loyalty", "coupon:FIX10")


@pytest.mark.ac("S4-AC2")
def test_fixed_coupon_without_loyalty_for_standard_customer():
    q = quote("100.00", customer=STANDARD, coupon=fixed("FIX10", "10"))
    # subtotal = 100.00, no loyalty; fixed 10.00 -> goods 90.00 -> free shipping
    # tax = 21% of 90.00 = 18.90
    # total = 100.00 - 10.00 + 0.00 + 18.90 = 108.90
    assert q.discount == D("10.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")
    assert q.applied == ("coupon:FIX10",)


@pytest.mark.ac("S4-AC2", "S3-AC2")
def test_fixed_coupon_is_taken_after_loyalty_and_cannot_push_goods_below_zero():
    q = quote("10.00", customer=GOLD, coupon=fixed("BIG", "9.80"))
    # subtotal = 10.00
    # loyalty = 5% of 10.00 = 0.50 -> goods 9.50
    # fixed 9.80 is taken after loyalty, capped so goods are not below 0.00 -> takes 9.50
    # discount = 0.50 + 9.50 = 10.00, goods = 0.00 (< 50.00) -> shipping 4.99
    # tax = 21% of (0.00 + 4.99) = 1.0479 -> 1.05
    # total = 10.00 - 10.00 + 4.99 + 1.05 = 6.04
    assert q.subtotal == D("10.00")
    assert q.discount == D("10.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("1.05")
    assert q.total == D("6.04")


@pytest.mark.ac("S4-AC2", "S6-AC3")
def test_applied_order_lists_volume_then_loyalty_then_fixed_coupon():
    catalog = {
        "A": Product(sku="A", name="Item A", unit_price=D("10.00")),
    }
    q = price_cart(
        [Line("A", 10)],
        catalog,
        today=TODAY,
        customer=GOLD,
        coupon=fixed("FIX5", "5"),
    )
    # line = 10 x 10.00 = 100.00; volume 10% off -> 90.00 = subtotal
    # loyalty = 5% of 90.00 = 4.50 -> 85.50; fixed 5.00 -> 80.50
    # discount = 4.50 + 5.00 = 9.50, goods = 80.50 -> free shipping
    # tax = 21% of 80.50 = 16.905 -> 16.91
    # total = 90.00 - 9.50 + 0.00 + 16.91 = 97.41
    assert q.subtotal == D("90.00")
    assert q.discount == D("9.50")
    assert q.tax == D("16.91")
    assert q.total == D("97.41")
    assert q.applied == ("volume:A", "loyalty", "coupon:FIX5")


@pytest.mark.ac("S4-AC1", "S1-AC5")
def test_gold_empty_cart_gets_no_loyalty_discount():
    q = price_cart([], {}, today=TODAY, customer=GOLD)
    # empty cart: every amount is 0.00, nothing applied
    assert q.subtotal == D("0.00")
    assert q.discount == D("0.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("0.00")
    assert q.total == D("0.00")
    assert q.applied == ()
```