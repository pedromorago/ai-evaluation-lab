```python
from datetime import date
from decimal import Decimal

import pytest

from checkout import (
    CartError,
    Coupon,
    Customer,
    Line,
    Product,
    price_cart,
)

TODAY = date(2026, 1, 15)


def D(value):
    return Decimal(value)


def single_item_catalog(price, sku="A", category="general"):
    return {sku: Product(sku=sku, name="Item " + sku, unit_price=D(price), category=category)}


def quote_for(price, quantity=1, **kwargs):
    return price_cart(
        [Line("A", quantity)],
        single_item_catalog(price),
        today=TODAY,
        **kwargs,
    )


# ---------------------------------------------------------------- S5-AC1


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_charged_just_below_free_threshold():
    # subtotal = 49.99 (1 x 49.99), no discount, goods = 49.99 < 50.00 -> shipping 4.99
    # tax = 21% of (49.99 + 4.99 = 54.98) = 11.5458 -> 11.55
    # total = 49.99 - 0.00 + 4.99 + 11.55 = 66.53
    q = quote_for("49.99")
    assert q.subtotal == D("49.99")
    assert q.shipping == D("4.99")
    assert q.tax == D("11.55")
    assert q.total == D("66.53")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_exactly_at_threshold():
    # subtotal = 50.00, goods = 50.00 >= 50.00 -> shipping 0.00
    # tax = 21% of (50.00 + 0.00) = 10.50
    # total = 50.00 - 0.00 + 0.00 + 10.50 = 60.50
    q = quote_for("50.00")
    assert q.subtotal == D("50.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("10.50")
    assert q.total == D("60.50")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_just_above_threshold():
    # subtotal = 50.01 >= 50.00 -> shipping 0.00
    # tax = 21% of 50.01 = 10.5021 -> 10.50
    # total = 50.01 + 0.00 + 10.50 = 60.51
    q = quote_for("50.01")
    assert q.shipping == D("0.00")
    assert q.tax == D("10.50")
    assert q.total == D("60.51")


@pytest.mark.ac("S5-AC1")
@pytest.mark.parametrize(
    "price, expected_shipping",
    [
        ("49.99", "4.99"),
        ("50.00", "0.00"),
        ("50.01", "0.00"),
        ("10.00", "4.99"),
        ("500.00", "0.00"),
    ],
)
def test_standard_shipping_threshold_table(price, expected_shipping):
    # shipping depends only on whether goods (no discounts here) reach 50.00
    q = quote_for(price)
    assert q.shipping == D(expected_shipping)


@pytest.mark.ac("S5-AC1")
def test_standard_is_the_default_shipping_method():
    # No shipping argument: default is "standard" -> 4.99 for goods of 20.00
    default = quote_for("20.00")
    explicit = quote_for("20.00", shipping="standard")
    assert default.shipping == D("4.99")
    assert explicit.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_free_shipping_threshold_uses_sum_of_several_lines():
    # 30.00 + 20.00 = 50.00 -> free
    catalog = {
        "A": Product("A", "A", D("30.00")),
        "B": Product("B", "B", D("20.00")),
    }
    q = price_cart([Line("A", 1), Line("B", 1)], catalog, today=TODAY)
    assert q.subtotal == D("50.00")
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_several_lines_just_below_threshold_pay_shipping():
    # 30.00 + 19.99 = 49.99 < 50.00 -> shipping 4.99
    catalog = {
        "A": Product("A", "A", D("30.00")),
        "B": Product("B", "B", D("19.99")),
    }
    q = price_cart([Line("A", 1), Line("B", 1)], catalog, today=TODAY)
    assert q.subtotal == D("49.99")
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_loyalty_discount_can_bring_goods_below_free_threshold():
    # subtotal = 52.00; gold 5% = 2.60; goods = 52.00 - 2.60 = 49.40 < 50.00 -> shipping 4.99
    # tax = 21% of (49.40 + 4.99 = 54.39) = 11.4219 -> 11.42
    # total = 52.00 - 2.60 + 4.99 + 11.42 = 65.81
    q = quote_for("52.00", customer=Customer(tier="gold"))
    assert q.subtotal == D("52.00")
    assert q.discount == D("2.60")
    assert q.shipping == D("4.99")
    assert q.tax == D("11.42")
    assert q.total == D("65.81")


@pytest.mark.ac("S5-AC1")
def test_loyalty_discounted_goods_still_above_threshold_ship_free():
    # subtotal = 53.00; gold 5% = 2.65; goods = 50.35 >= 50.00 -> shipping 0.00
    # tax = 21% of 50.35 = 10.5735 -> 10.57
    # total = 53.00 - 2.65 + 0.00 + 10.57 = 60.92
    q = quote_for("53.00", customer=Customer(tier="gold"))
    assert q.discount == D("2.65")
    assert q.shipping == D("0.00")
    assert q.tax == D("10.57")
    assert q.total == D("60.92")


@pytest.mark.ac("S5-AC1")
def test_percent_coupon_taking_goods_below_threshold_charges_shipping():
    # subtotal = 60.00; 20% coupon = 12.00; goods = 48.00 < 50.00 -> shipping 4.99
    # tax = 21% of (48.00 + 4.99 = 52.99) = 11.1279 -> 11.13
    # total = 60.00 - 12.00 + 4.99 + 11.13 = 64.12
    q = quote_for("60.00", coupon=Coupon("TWENTY", "percent", D("20")))
    assert q.discount == D("12.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("11.13")
    assert q.total == D("64.12")


@pytest.mark.ac("S5-AC1")
def test_percent_coupon_leaving_goods_exactly_at_threshold_ships_free():
    # subtotal = 62.50; 20% coupon = 12.50; goods = 50.00 >= 50.00 -> shipping 0.00
    # tax = 21% of 50.00 = 10.50
    # total = 62.50 - 12.50 + 0.00 + 10.50 = 60.50
    q = quote_for("62.50", coupon=Coupon("TWENTY", "percent", D("20")))
    assert q.discount == D("12.50")
    assert q.shipping == D("0.00")
    assert q.tax == D("10.50")
    assert q.total == D("60.50")


@pytest.mark.ac("S5-AC1")
def test_percent_coupon_goods_clearly_below_threshold_charges_shipping():
    # subtotal = 62.00; 20% coupon = 12.40; goods = 49.60 < 50.00 -> shipping 4.99
    q = quote_for("62.00", coupon=Coupon("TWENTY", "percent", D("20")))
    assert q.discount == D("12.40")
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_percent_coupon_with_goods_above_threshold_ships_free():
    # subtotal = 60.00; 10% = 6.00; goods = 54.00 >= 50.00 -> shipping 0.00
    # tax = 21% of 54.00 = 11.34
    # total = 60.00 - 6.00 + 0.00 + 11.34 = 65.34
    q = quote_for("60.00", coupon=Coupon("SAVE10", "percent", D("10")))
    assert q.shipping == D("0.00")
    assert q.tax == D("11.34")
    assert q.total == D("65.34")


@pytest.mark.ac("S5-AC1")
@pytest.mark.parametrize(
    "coupon_value, expected_shipping",
    [
        ("4.99", "0.00"),  # goods 50.01
        ("5.00", "0.00"),  # goods 50.00
        ("5.01", "4.99"),  # goods 49.99
    ],
)
def test_fixed_coupon_around_free_shipping_threshold(coupon_value, expected_shipping):
    # subtotal = 55.00; goods = 55.00 - coupon_value
    #   4.99 -> 50.01 (free), 5.00 -> 50.00 (free), 5.01 -> 49.99 (shipping 4.99)
    q = quote_for("55.00", coupon=Coupon("FIX", "fixed", D(coupon_value)))
    assert q.shipping == D(expected_shipping)


@pytest.mark.ac("S5-AC1")
def test_fixed_coupon_below_threshold_full_quote():
    # subtotal = 55.00; fixed 5.01 -> goods = 49.99 < 50.00 -> shipping 4.99
    # tax = 21% of (49.99 + 4.99 = 54.98) = 11.5458 -> 11.55
    # total = 55.00 - 5.01 + 4.99 + 11.55 = 66.53
    q = quote_for("55.00", coupon=Coupon("FIX", "fixed", D("5.01")))
    assert q.discount == D("5.01")
    assert q.shipping == D("4.99")
    assert q.tax == D("11.55")
    assert q.total == D("66.53")


@pytest.mark.ac("S5-AC1")
def test_loyalty_plus_fixed_coupon_exactly_at_threshold_ships_free():
    # subtotal = 60.00; gold 5% = 3.00; fixed 7.00 after it; discount = 10.00
    # goods = 60.00 - 10.00 = 50.00 >= 50.00 -> shipping 0.00
    q = quote_for(
        "60.00",
        customer=Customer(tier="gold"),
        coupon=Coupon("FIX", "fixed", D("7.00")),
    )
    assert q.discount == D("10.00")
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_loyalty_plus_fixed_coupon_one_cent_below_threshold_charges_shipping():
    # subtotal = 60.00; gold 5% = 3.00; fixed 7.01; discount = 10.01
    # goods = 49.99 < 50.00 -> shipping 4.99
    q = quote_for(
        "60.00",
        customer=Customer(tier="gold"),
        coupon=Coupon("FIX", "fixed", D("7.01")),
    )
    assert q.discount == D("10.01")
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_volume_discount_counts_towards_free_shipping_threshold():
    # 10 x 5.50 = 55.00; volume 10% off the line = 5.50; subtotal = 49.50
    # goods = 49.50 < 50.00 -> shipping 4.99 (it would be free without the volume discount)
    # tax = 21% of (49.50 + 4.99 = 54.49) = 11.4429 -> 11.44
    # total = 49.50 - 0.00 + 4.99 + 11.44 = 65.93
    q = quote_for("5.50", quantity=10)
    assert q.subtotal == D("49.50")
    assert q.shipping == D("4.99")
    assert q.tax == D("11.44")
    assert q.total == D("65.93")


@pytest.mark.ac("S5-AC1")
def test_fixed_coupon_wiping_out_goods_still_charges_standard_shipping():
    # subtotal = 20.00; fixed 100.00 can't take goods below 0.00 -> discount 20.00, goods 0.00
    # shipping = 4.99 (goods < 50.00)
    # tax = 21% of (0.00 + 4.99) = 1.0479 -> 1.05
    # total = 20.00 - 20.00 + 4.99 + 1.05 = 6.04
    q = quote_for("20.00", coupon=Coupon("BIG", "fixed", D("100.00")))
    assert q.discount == D("20.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("1.05")
    assert q.total == D("6.04")


# ---------------------------------------------------------------- S5-AC2


@pytest.mark.ac("S5-AC2")
def test_express_shipping_costs_9_99_on_small_order():
    # subtotal = 20.00; express = 9.99
    # tax = 21% of (20.00 + 9.99 = 29.99) = 6.2979 -> 6.30
    # total = 20.00 + 9.99 + 6.30 = 36.29
    q = quote_for("20.00", shipping="express")
    assert q.shipping == D("9.99")
    assert q.tax == D("6.30")
    assert q.total == D("36.29")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_not_free_exactly_at_standard_free_threshold():
    # subtotal = 50.00; express is never free -> 9.99
    # tax = 21% of (50.00 + 9.99 = 59.99) = 12.5979 -> 12.60
    # total = 50.00 + 9.99 + 12.60 = 72.59
    q = quote_for("50.00", shipping="express")
    assert q.shipping == D("9.99")
    assert q.tax == D("12.60")
    assert q.total == D("72.59")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_not_free_on_large_order():
    # subtotal = 100.00; express -> 9.99
    # tax = 21% of (100.00 + 9.99 = 109.99) = 23.0979 -> 23.10
    # total = 100.00 + 9.99 + 23.10 = 133.09
    q = quote_for("100.00", shipping="express")
    assert q.shipping == D("9.99")
    assert q.tax == D("23.10")
    assert q.total == D("133.09")


@pytest.mark.ac("S5-AC2")
@pytest.mark.parametrize("price", ["49.99", "50.00", "50.01", "1000.00"])
def test_express_shipping_is_always_9_99_around_threshold(price):
    q = quote_for(price, shipping="express")
    assert q.shipping == D("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_not_free_for_gold_customer_with_coupon_on_big_cart():
    # subtotal = 200.00; gold 5% = 10.00; fixed coupon 10.00 stacks; discount = 20.00
    # goods = 180.00; express -> 9.99
    # tax = 21% of (180.00 + 9.99 = 189.99) = 39.8979 -> 39.90
    # total = 200.00 - 20.00 + 9.99 + 39.90 = 229.89
    q = quote_for(
        "200.00",
        customer=Customer(tier="gold"),
        coupon=Coupon("FIX", "fixed", D("10.00")),
        shipping="express",
    )
    assert q.discount == D("20.00")
    assert q.shipping == D("9.99")
    assert q.tax == D("39.90")
    assert q.total == D("229.89")


# ---------------------------------------------------------------- S5-AC3


@pytest.mark.ac("S5-AC3")
@pytest.mark.parametrize("method", ["overnight", "pickup", "free", ""])
def test_unknown_shipping_method_raises_cart_error(method):
    with pytest.raises(CartError):
        quote_for("20.00", shipping=method)


@pytest.mark.ac("S5-AC3")
def test_unknown_shipping_method_raises_cart_error_even_when_goods_qualify_for_free_shipping():
    with pytest.raises(CartError):
        quote_for("100.00", shipping="overnight")


@pytest.mark.ac("S5-AC3")
def test_unknown_shipping_method_raises_cart_error_with_coupon_and_gold_customer():
    with pytest.raises(CartError):
        quote_for(
            "80.00",
            customer=Customer(tier="gold"),
            coupon=Coupon("SAVE10", "percent", D("10")),
            shipping="drone",
        )
```