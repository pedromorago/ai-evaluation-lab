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

TODAY = date(2026, 10, 3)
D = Decimal


def make_catalog():
    products = [
        Product("P20", "Twenty", D("20.00")),
        Product("P100", "Hundred", D("100.00")),
        Product("P55", "Fifty five", D("55.00")),
        Product("P1051", "Odd price", D("10.51")),
        Product("P1010", "Ten ten", D("10.10")),
        Product("P055", "Cheap", D("0.55")),
        Product("P10", "Ten", D("10.00")),
        Product("ZED", "Zed", D("1.00")),
        Product("ALPHA", "Alpha", D("1.00")),
        Product("PLAIN", "Plain", D("1.00")),
        Product("BK", "Book", D("5.00"), category="books"),
    ]
    return {p.sku: p for p in products}


def price(lines, **kwargs):
    return price_cart(lines, make_catalog(), today=TODAY, **kwargs)


def percent(code, value):
    return Coupon(code=code, kind="percent", value=D(value))


def fixed(code, value):
    return Coupon(code=code, kind="fixed", value=D(value))


# ---------------------------------------------------------------- S6-AC1


@pytest.mark.ac("S6-AC1")
def test_vat_is_21_percent_of_goods_plus_standard_shipping():
    # goods = 20.00, shipping = 4.99 (goods < 50.00)
    # tax = 0.21 * (20.00 + 4.99) = 0.21 * 24.99 = 5.2479 -> 5.25
    # total = 20.00 - 0.00 + 4.99 + 5.25 = 30.24
    q = price([Line("P20", 1)])
    assert q.subtotal == D("20.00")
    assert q.discount == D("0.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("5.25")
    assert q.total == D("30.24")


@pytest.mark.ac("S6-AC1")
def test_vat_with_free_shipping_applies_only_to_goods():
    # goods = 100.00, shipping = 0.00 (free, goods >= 50.00)
    # tax = 0.21 * 100.00 = 21.00
    # total = 100.00 - 0.00 + 0.00 + 21.00 = 121.00
    q = price([Line("P100", 1)])
    assert q.subtotal == D("100.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("21.00")
    assert q.total == D("121.00")


@pytest.mark.ac("S6-AC1")
def test_vat_includes_express_shipping():
    # goods = 100.00, express shipping = 9.99
    # tax = 0.21 * (100.00 + 9.99) = 0.21 * 109.99 = 23.0979 -> 23.10
    # total = 100.00 - 0.00 + 9.99 + 23.10 = 133.09
    q = price([Line("P100", 1)], shipping="express")
    assert q.shipping == D("9.99")
    assert q.tax == D("23.10")
    assert q.total == D("133.09")


@pytest.mark.ac("S6-AC1")
def test_vat_is_computed_on_goods_after_percent_coupon():
    # subtotal = 100.00; coupon 10% -> discount 10.00; goods = 90.00
    # shipping free (90.00 >= 50.00)
    # tax = 0.21 * 90.00 = 18.90
    # total = 100.00 - 10.00 + 0.00 + 18.90 = 108.90
    q = price([Line("P100", 1)], coupon=percent("SAVE10", "10"))
    assert q.subtotal == D("100.00")
    assert q.discount == D("10.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")


@pytest.mark.ac("S6-AC1")
def test_vat_is_computed_on_goods_after_volume_discount_and_coupon():
    # line: 10 x 10.00 = 100.00, volume 10% off -> subtotal 90.00
    # coupon 10% of 90.00 = 9.00; goods = 81.00; shipping free
    # tax = 0.21 * 81.00 = 17.01
    # total = 90.00 - 9.00 + 0.00 + 17.01 = 98.01
    q = price([Line("P10", 10)], coupon=percent("SAVE10", "10"))
    assert q.subtotal == D("90.00")
    assert q.discount == D("9.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("17.01")
    assert q.total == D("98.01")


@pytest.mark.ac("S6-AC1")
def test_vat_when_fixed_coupon_pushes_goods_below_free_shipping():
    # subtotal = 55.00; fixed coupon 10.00 -> goods = 45.00 (< 50.00)
    # shipping = 4.99
    # tax = 0.21 * (45.00 + 4.99) = 0.21 * 49.99 = 10.4979 -> 10.50
    # total = 55.00 - 10.00 + 4.99 + 10.50 = 60.49
    q = price([Line("P55", 1)], coupon=fixed("TEN", "10.00"))
    assert q.subtotal == D("55.00")
    assert q.discount == D("10.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("10.50")
    assert q.total == D("60.49")


# ---------------------------------------------------------------- S6-AC2


@pytest.mark.ac("S6-AC2")
def test_tax_exactly_half_a_cent_rounds_up():
    # subtotal = 10.51, express shipping = 9.99
    # tax base = 10.51 + 9.99 = 20.50
    # tax = 0.21 * 20.50 = 4.305 -> half up -> 4.31
    # total = 10.51 - 0.00 + 9.99 + 4.31 = 24.81
    q = price([Line("P1051", 1)], shipping="express")
    assert q.subtotal == D("10.51")
    assert q.discount == D("0.00")
    assert q.shipping == D("9.99")
    assert q.tax == D("4.31")
    assert q.total == D("24.81")


@pytest.mark.ac("S6-AC2")
def test_subtotal_after_volume_discount_exactly_half_a_cent_rounds_up():
    # line: 11 x 0.55 = 6.05; volume 10% off -> 6.05 * 0.90 = 5.445
    # half up -> subtotal 5.45
    # goods = 5.45, shipping = 4.99
    # tax = 0.21 * (5.45 + 4.99) = 0.21 * 10.44 = 2.1924 -> 2.19
    # total = 5.45 - 0.00 + 4.99 + 2.19 = 12.63
    q = price([Line("P055", 11)])
    assert q.subtotal == D("5.45")
    assert q.discount == D("0.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("2.19")
    assert q.total == D("12.63")


@pytest.mark.ac("S6-AC2")
def test_loyalty_discount_exactly_half_a_cent_rounds_up():
    # subtotal = 10.10; gold 5% -> 10.10 * 0.05 = 0.505 -> half up -> 0.51
    # goods = 10.10 - 0.51 = 9.59, shipping = 4.99
    # tax = 0.21 * (9.59 + 4.99) = 0.21 * 14.58 = 3.0618 -> 3.06
    # total = 10.10 - 0.51 + 4.99 + 3.06 = 17.64
    q = price([Line("P1010", 1)], customer=Customer(tier="gold"))
    assert q.subtotal == D("10.10")
    assert q.discount == D("0.51")
    assert q.shipping == D("4.99")
    assert q.tax == D("3.06")
    assert q.total == D("17.64")


@pytest.mark.ac("S6-AC2")
def test_percent_coupon_discount_exactly_half_a_cent_rounds_up():
    # subtotal = 10.10; coupon 5% -> 0.505 -> half up -> 0.51
    # goods = 10.10 - 0.51 = 9.59, shipping = 4.99
    # tax = 0.21 * 14.58 = 3.0618 -> 3.06
    # total = 10.10 - 0.51 + 4.99 + 3.06 = 17.64
    q = price([Line("P1010", 1)], coupon=percent("FIVE", "5"))
    assert q.discount == D("0.51")
    assert q.tax == D("3.06")
    assert q.total == D("17.64")


@pytest.mark.ac("S6-AC2")
def test_each_discount_is_rounded_then_added_and_total_is_exact_sum():
    # subtotal = 10.10
    # loyalty 5% = 0.505 -> 0.51; fixed coupon = 1.00
    # discount = 0.51 + 1.00 = 1.51; goods = 10.10 - 1.51 = 8.59
    # shipping = 4.99
    # tax = 0.21 * (8.59 + 4.99) = 0.21 * 13.58 = 2.8518 -> 2.85
    # total = 10.10 - 1.51 + 4.99 + 2.85 = 16.43
    q = price(
        [Line("P1010", 1)],
        customer=Customer(tier="gold"),
        coupon=fixed("ONE", "1.00"),
    )
    assert q.subtotal == D("10.10")
    assert q.discount == D("1.51")
    assert q.shipping == D("4.99")
    assert q.tax == D("2.85")
    assert q.total == D("16.43")
    assert q.total == q.subtotal - q.discount + q.shipping + q.tax


@pytest.mark.ac("S6-AC2")
def test_loyalty_and_fixed_coupon_discount_reported_together():
    # subtotal = 100.00; gold 5% = 5.00; fixed 2.00 after it
    # discount = 5.00 + 2.00 = 7.00; goods = 93.00; shipping free
    # tax = 0.21 * 93.00 = 19.53
    # total = 100.00 - 7.00 + 0.00 + 19.53 = 112.53
    q = price(
        [Line("P100", 1)],
        customer=Customer(tier="gold"),
        coupon=fixed("TWO", "2.00"),
    )
    assert q.subtotal == D("100.00")
    assert q.discount == D("7.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("19.53")
    assert q.total == D("112.53")


# ---------------------------------------------------------------- S6-AC3


@pytest.mark.ac("S6-AC3")
def test_applied_is_empty_without_any_discount():
    q = price([Line("P20", 1)])
    assert q.applied == ()


@pytest.mark.ac("S6-AC3")
def test_applied_lists_volume_discounts_in_cart_order_not_sorted():
    # ZED appears first in the cart, then PLAIN (no discount), then ALPHA.
    q = price([Line("ZED", 10), Line("PLAIN", 1), Line("ALPHA", 50)])
    assert q.applied == ("volume:ZED", "volume:ALPHA")


@pytest.mark.ac("S6-AC3")
def test_applied_volume_order_follows_first_appearance_of_merged_lines():
    # ZED first appears at index 0, ALPHA at index 1, ZED again at index 2.
    # Merged: ZED 10 units, ALPHA 10 units -> both discounted.
    q = price([Line("ZED", 5), Line("ALPHA", 10), Line("ZED", 5)])
    assert q.applied == ("volume:ZED", "volume:ALPHA")


@pytest.mark.ac("S6-AC3")
def test_applied_does_not_list_books_or_undiscounted_products():
    # 10 books get no volume discount; 9 units are below the threshold.
    q = price([Line("BK", 10), Line("ZED", 9)])
    assert q.applied == ()


@pytest.mark.ac("S6-AC3")
def test_applied_lists_loyalty_for_gold_customer():
    q = price([Line("P20", 1)], customer=Customer(tier="gold"))
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S6-AC3")
def test_applied_lists_percent_coupon_alone():
    q = price([Line("P20", 1)], coupon=percent("SAVE10", "10"))
    assert q.applied == ("coupon:SAVE10",)


@pytest.mark.ac("S6-AC3")
def test_applied_lists_only_coupon_when_percent_coupon_beats_loyalty():
    # gold 5% vs coupon 10% -> coupon wins
    q = price(
        [Line("P20", 1)],
        customer=Customer(tier="gold"),
        coupon=percent("SAVE10", "10"),
    )
    assert q.applied == ("coupon:SAVE10",)


@pytest.mark.ac("S6-AC3")
def test_applied_lists_only_loyalty_when_loyalty_beats_percent_coupon():
    # gold 5% vs coupon 2% -> loyalty wins
    q = price(
        [Line("P20", 1)],
        customer=Customer(tier="gold"),
        coupon=percent("TWO", "2"),
    )
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S6-AC3")
def test_applied_lists_coupon_not_loyalty_when_percentages_are_equal():
    # gold 5% vs coupon 5% -> coupon wins ties
    q = price(
        [Line("P20", 1)],
        customer=Customer(tier="gold"),
        coupon=percent("FIVE", "5"),
    )
    assert q.applied == ("coupon:FIVE",)


@pytest.mark.ac("S6-AC3")
def test_applied_lists_fixed_coupon_alone():
    q = price([Line("P20", 1)], coupon=fixed("FIX", "2.00"))
    assert q.applied == ("coupon:FIX",)


@pytest.mark.ac("S6-AC3")
def test_applied_lists_loyalty_before_fixed_coupon():
    q = price(
        [Line("P20", 1)],
        customer=Customer(tier="gold"),
        coupon=fixed("FIX", "2.00"),
    )
    assert q.applied == ("loyalty", "coupon:FIX")


@pytest.mark.ac("S6-AC3")
def test_applied_orders_volume_then_loyalty_then_fixed_coupon():
    q = price(
        [Line("ZED", 10), Line("BK", 10), Line("ALPHA", 50)],
        customer=Customer(tier="gold"),
        coupon=fixed("FIX", "2.00"),
    )
    assert q.applied == ("volume:ZED", "volume:ALPHA", "loyalty", "coupon:FIX")


@pytest.mark.ac("S6-AC3")
def test_applied_orders_volume_before_winning_percent_coupon():
    q = price(
        [Line("ZED", 10)],
        customer=Customer(tier="gold"),
        coupon=percent("SAVE10", "10"),
    )
    assert q.applied == ("volume:ZED", "coupon:SAVE10")


@pytest.mark.ac("S6-AC3")
def test_applied_does_not_list_loyalty_for_standard_customer():
    q = price(
        [Line("ZED", 10)],
        customer=Customer(tier="standard"),
        coupon=fixed("FIX", "1.00"),
    )
    assert q.applied == ("volume:ZED", "coupon:FIX")
