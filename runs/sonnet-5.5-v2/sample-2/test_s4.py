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

TODAY = date(2025, 1, 15)

D = Decimal


def _catalog(price="100.00", sku="A", category="general"):
    return {sku: Product(sku=sku, name="Item " + sku, unit_price=D(price), category=category)}


def _pct(code, value):
    return Coupon(code=code, kind="percent", value=D(value))


def _fixed(code, value):
    return Coupon(code=code, kind="fixed", value=D(value))


# ---------------------------------------------------------------- S4-AC1


@pytest.mark.ac("S4-AC1")
def test_gold_customer_gets_five_percent_off_subtotal():
    # subtotal = 1 * 100.00 = 100.00
    # loyalty = 5% of 100.00 = 5.00
    # goods = 100.00 - 5.00 = 95.00 -> >= 50.00, shipping free = 0.00
    # tax = 21% of (95.00 + 0.00) = 19.95
    # total = 100.00 - 5.00 + 0.00 + 19.95 = 114.95
    q = price_cart(
        [Line("A", 1)],
        _catalog("100.00"),
        today=TODAY,
        customer=Customer(tier="gold"),
    )
    assert q.subtotal == D("100.00")
    assert q.discount == D("5.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("19.95")
    assert q.total == D("114.95")
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S4-AC1")
def test_standard_customer_gets_no_loyalty_discount():
    # subtotal = 100.00, discount = 0.00
    # goods = 100.00 -> shipping free = 0.00
    # tax = 21% of 100.00 = 21.00
    # total = 100.00 - 0.00 + 0.00 + 21.00 = 121.00
    q = price_cart(
        [Line("A", 1)],
        _catalog("100.00"),
        today=TODAY,
        customer=Customer(tier="standard"),
    )
    assert q.subtotal == D("100.00")
    assert q.discount == D("0.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("21.00")
    assert q.total == D("121.00")
    assert q.applied == ()


@pytest.mark.ac("S4-AC1")
def test_default_customer_gets_no_loyalty_discount():
    # default customer is standard: no discount.
    # subtotal = 40.00, discount = 0.00
    # goods = 40.00 < 50.00 -> shipping 4.99
    # tax = 21% of (40.00 + 4.99) = 21% of 44.99 = 9.4479 -> 9.45
    # total = 40.00 - 0.00 + 4.99 + 9.45 = 54.44
    q = price_cart([Line("A", 1)], _catalog("40.00"), today=TODAY)
    assert q.discount == D("0.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("9.45")
    assert q.total == D("54.44")
    assert q.applied == ()


@pytest.mark.ac("S4-AC1")
def test_loyalty_discount_is_rounded_half_up_to_the_cent():
    # subtotal = 10.10
    # loyalty = 5% of 10.10 = 0.505 -> half up = 0.51
    # goods = 10.10 - 0.51 = 9.59 -> < 50.00, shipping 4.99
    # tax = 21% of (9.59 + 4.99) = 21% of 14.58 = 3.0618 -> 3.06
    # total = 10.10 - 0.51 + 4.99 + 3.06 = 17.64
    q = price_cart(
        [Line("A", 1)],
        _catalog("10.10"),
        today=TODAY,
        customer=Customer(tier="gold"),
    )
    assert q.subtotal == D("10.10")
    assert q.discount == D("0.51")
    assert q.shipping == D("4.99")
    assert q.tax == D("3.06")
    assert q.total == D("17.64")


@pytest.mark.ac("S4-AC1", "S2-AC1", "S6-AC3")
def test_loyalty_applies_on_subtotal_after_volume_discount():
    # line = 10 * 10.00 = 100.00, volume 10% off -> subtotal = 90.00
    # loyalty = 5% of 90.00 = 4.50
    # goods = 90.00 - 4.50 = 85.50 -> shipping free = 0.00
    # tax = 21% of 85.50 = 17.955 -> 17.96
    # total = 90.00 - 4.50 + 0.00 + 17.96 = 103.46
    q = price_cart(
        [Line("A", 10)],
        _catalog("10.00"),
        today=TODAY,
        customer=Customer(tier="gold"),
    )
    assert q.subtotal == D("90.00")
    assert q.discount == D("4.50")
    assert q.shipping == D("0.00")
    assert q.tax == D("17.96")
    assert q.total == D("103.46")
    assert q.applied == ("volume:A", "loyalty")


# ---------------------------------------------------------------- S4-AC2


@pytest.mark.ac("S4-AC2")
def test_gold_with_larger_percent_coupon_only_coupon_applies():
    # subtotal = 100.00
    # loyalty = 5% = 5.00; coupon = 10% = 10.00 -> coupon is larger, only it applies
    # discount = 10.00 (not 15.00)
    # goods = 90.00 -> shipping free = 0.00
    # tax = 21% of 90.00 = 18.90
    # total = 100.00 - 10.00 + 0.00 + 18.90 = 108.90
    q = price_cart(
        [Line("A", 1)],
        _catalog("100.00"),
        today=TODAY,
        customer=Customer(tier="gold"),
        coupon=_pct("SAVE10", "10"),
    )
    assert q.subtotal == D("100.00")
    assert q.discount == D("10.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")
    assert q.applied == ("coupon:SAVE10",)


@pytest.mark.ac("S4-AC2")
def test_gold_with_smaller_percent_coupon_only_loyalty_applies():
    # subtotal = 100.00
    # loyalty = 5% = 5.00; coupon = 3% = 3.00 -> loyalty is larger, only it applies
    # discount = 5.00
    # goods = 95.00 -> shipping free = 0.00
    # tax = 21% of 95.00 = 19.95
    # total = 100.00 - 5.00 + 0.00 + 19.95 = 114.95
    q = price_cart(
        [Line("A", 1)],
        _catalog("100.00"),
        today=TODAY,
        customer=Customer(tier="gold"),
        coupon=_pct("SMALL3", "3"),
    )
    assert q.discount == D("5.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("19.95")
    assert q.total == D("114.95")
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S4-AC2")
def test_gold_with_equal_percent_coupon_coupon_wins_the_tie():
    # subtotal = 100.00
    # loyalty = 5% = 5.00; coupon = 5% = 5.00 -> equal, the coupon applies
    # discount = 5.00
    # goods = 95.00 -> shipping free = 0.00
    # tax = 21% of 95.00 = 19.95
    # total = 100.00 - 5.00 + 0.00 + 19.95 = 114.95
    q = price_cart(
        [Line("A", 1)],
        _catalog("100.00"),
        today=TODAY,
        customer=Customer(tier="gold"),
        coupon=_pct("FIVE", "5"),
    )
    assert q.discount == D("5.00")
    assert q.tax == D("19.95")
    assert q.total == D("114.95")
    assert q.applied == ("coupon:FIVE",)


@pytest.mark.ac("S4-AC2")
def test_gold_percent_coupon_just_above_loyalty_wins():
    # subtotal = 200.00
    # loyalty = 5% = 10.00; coupon = 6% = 12.00 -> coupon is larger
    # discount = 12.00
    # goods = 188.00 -> shipping free = 0.00
    # tax = 21% of 188.00 = 39.48
    # total = 200.00 - 12.00 + 0.00 + 39.48 = 227.48
    q = price_cart(
        [Line("A", 2)],
        _catalog("100.00"),
        today=TODAY,
        customer=Customer(tier="gold"),
        coupon=_pct("SIX", "6"),
    )
    assert q.discount == D("12.00")
    assert q.tax == D("39.48")
    assert q.total == D("227.48")
    assert q.applied == ("coupon:SIX",)


@pytest.mark.ac("S4-AC2")
def test_gold_percent_coupon_just_below_loyalty_loses():
    # subtotal = 200.00
    # loyalty = 5% = 10.00; coupon = 4% = 8.00 -> loyalty is larger
    # discount = 10.00
    # goods = 190.00 -> shipping free = 0.00
    # tax = 21% of 190.00 = 39.90
    # total = 200.00 - 10.00 + 0.00 + 39.90 = 229.90
    q = price_cart(
        [Line("A", 2)],
        _catalog("100.00"),
        today=TODAY,
        customer=Customer(tier="gold"),
        coupon=_pct("FOUR", "4"),
    )
    assert q.discount == D("10.00")
    assert q.tax == D("39.90")
    assert q.total == D("229.90")
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S4-AC2")
def test_standard_customer_percent_coupon_applies_alone():
    # subtotal = 100.00; no loyalty for standard
    # coupon = 10% = 10.00
    # goods = 90.00 -> shipping free = 0.00
    # tax = 21% of 90.00 = 18.90
    # total = 100.00 - 10.00 + 0.00 + 18.90 = 108.90
    q = price_cart(
        [Line("A", 1)],
        _catalog("100.00"),
        today=TODAY,
        customer=Customer(tier="standard"),
        coupon=_pct("SAVE10", "10"),
    )
    assert q.discount == D("10.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")
    assert q.applied == ("coupon:SAVE10",)


@pytest.mark.ac("S4-AC2", "S6-AC3")
def test_fixed_coupon_stacks_with_loyalty_and_comes_after_it():
    # subtotal = 100.00
    # loyalty = 5% of 100.00 = 5.00 (taken first, on the full subtotal)
    # fixed coupon = 10.00 taken off after loyalty
    # discount = 5.00 + 10.00 = 15.00
    # goods = 100.00 - 15.00 = 85.00 -> shipping free = 0.00
    # tax = 21% of 85.00 = 17.85
    # total = 100.00 - 15.00 + 0.00 + 17.85 = 102.85
    q = price_cart(
        [Line("A", 1)],
        _catalog("100.00"),
        today=TODAY,
        customer=Customer(tier="gold"),
        coupon=_fixed("FIX10", "10"),
    )
    assert q.subtotal == D("100.00")
    assert q.discount == D("15.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("17.85")
    assert q.total == D("102.85")
    assert q.applied == ("loyalty", "coupon:FIX10")


@pytest.mark.ac("S4-AC2")
def test_fixed_coupon_with_standard_customer_has_no_loyalty():
    # subtotal = 100.00, no loyalty
    # fixed coupon = 10.00 -> discount = 10.00
    # goods = 90.00 -> shipping free = 0.00
    # tax = 21% of 90.00 = 18.90
    # total = 100.00 - 10.00 + 0.00 + 18.90 = 108.90
    q = price_cart(
        [Line("A", 1)],
        _catalog("100.00"),
        today=TODAY,
        customer=Customer(tier="standard"),
        coupon=_fixed("FIX10", "10"),
    )
    assert q.discount == D("10.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")
    assert q.applied == ("coupon:FIX10",)


@pytest.mark.ac("S4-AC2")
def test_fixed_coupon_after_loyalty_never_takes_goods_below_zero():
    # subtotal = 10.00
    # loyalty = 5% = 0.50 -> goods 9.50
    # fixed coupon = 20.00, capped so goods stay at 0.00 -> takes 9.50
    # discount = 0.50 + 9.50 = 10.00
    # goods = 0.00 -> < 50.00, shipping 4.99
    # tax = 21% of (0.00 + 4.99) = 1.0479 -> 1.05
    # total = 10.00 - 10.00 + 4.99 + 1.05 = 6.04
    q = price_cart(
        [Line("A", 1)],
        _catalog("10.00"),
        today=TODAY,
        customer=Customer(tier="gold"),
        coupon=_fixed("BIG20", "20"),
    )
    assert q.subtotal == D("10.00")
    assert q.discount == D("10.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("1.05")
    assert q.total == D("6.04")
    assert q.applied == ("loyalty", "coupon:BIG20")


@pytest.mark.ac("S4-AC2", "S6-AC3")
def test_applied_order_volume_then_loyalty_then_fixed_coupon():
    # A: 10 * 10.00 = 100.00, volume 10% off -> 90.00
    # B: 1 * 10.00 = 10.00 (no volume)
    # subtotal = 90.00 + 10.00 = 100.00
    # loyalty = 5% of 100.00 = 5.00
    # fixed coupon = 5.00
    # discount = 10.00
    # goods = 90.00 -> shipping free = 0.00
    # tax = 21% of 90.00 = 18.90
    # total = 100.00 - 10.00 + 0.00 + 18.90 = 108.90
    catalog = {
        "A": Product("A", "Item A", D("10.00")),
        "B": Product("B", "Item B", D("10.00")),
    }
    q = price_cart(
        [Line("A", 10), Line("B", 1)],
        catalog,
        today=TODAY,
        customer=Customer(tier="gold"),
        coupon=_fixed("FIX5", "5"),
    )
    assert q.subtotal == D("100.00")
    assert q.discount == D("10.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")
    assert q.applied == ("volume:A", "loyalty", "coupon:FIX5")
