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


def D(value):
    return Decimal(value)


def catalog_of(*products):
    return {p.sku: p for p in products}


def single(price, qty=1, sku="A", category="general", **kwargs):
    """Price a cart with one product."""
    cat = catalog_of(Product(sku, "Item " + sku, D(price), category))
    return price_cart([Line(sku, qty)], cat, today=TODAY, **kwargs)


# ---------------------------------------------------------------- S6-AC1: VAT


@pytest.mark.ac("S6-AC1", "S6-AC2")
def test_vat_covers_goods_and_standard_shipping_when_shipping_is_charged():
    # subtotal = 10.00, discount = 0.00, goods < 50 so shipping = 4.99
    # taxable = 10.00 + 4.99 = 14.99
    # tax = 14.99 * 0.21 = 3.1479 -> 3.15
    # total = 10.00 - 0.00 + 4.99 + 3.15 = 18.14
    q = single("10.00")
    assert q.subtotal == D("10.00")
    assert q.discount == D("0.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("3.15")
    assert q.total == D("18.14")


@pytest.mark.ac("S6-AC1", "S6-AC2")
def test_vat_covers_express_shipping():
    # subtotal = 100.00, express shipping = 9.99 (never free)
    # taxable = 100.00 + 9.99 = 109.99
    # tax = 109.99 * 0.21 = 23.0979 -> 23.10
    # total = 100.00 - 0.00 + 9.99 + 23.10 = 133.09
    q = single("100.00", shipping="express")
    assert q.subtotal == D("100.00")
    assert q.shipping == D("9.99")
    assert q.tax == D("23.10")
    assert q.total == D("133.09")


@pytest.mark.ac("S6-AC1", "S6-AC2")
def test_vat_with_free_shipping_is_21_percent_of_goods_only():
    # subtotal = 100.00, goods >= 50 so standard shipping = 0.00
    # taxable = 100.00 + 0.00 = 100.00
    # tax = 100.00 * 0.21 = 21.00
    # total = 100.00 - 0.00 + 0.00 + 21.00 = 121.00
    q = single("100.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("21.00")
    assert q.total == D("121.00")


@pytest.mark.ac("S6-AC1", "S6-AC2")
def test_vat_is_computed_on_goods_after_percent_coupon():
    # subtotal = 100.00; coupon 10% -> discount = 10.00
    # goods after discount = 90.00 >= 50 so shipping = 0.00
    # taxable = 90.00 + 0.00 = 90.00
    # tax = 90.00 * 0.21 = 18.90
    # total = 100.00 - 10.00 + 0.00 + 18.90 = 108.90
    coupon = Coupon("SAVE10", "percent", D("10"))
    q = single("100.00", coupon=coupon)
    assert q.subtotal == D("100.00")
    assert q.discount == D("10.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")


@pytest.mark.ac("S6-AC1", "S6-AC2")
def test_vat_is_computed_on_goods_after_loyalty_discount_with_shipping():
    # subtotal = 20.00; gold 5% -> discount = 1.00
    # goods after discount = 19.00 < 50 so shipping = 4.99
    # taxable = 19.00 + 4.99 = 23.99
    # tax = 23.99 * 0.21 = 5.0379 -> 5.04
    # total = 20.00 - 1.00 + 4.99 + 5.04 = 29.03
    q = single("20.00", customer=Customer(tier="gold"))
    assert q.subtotal == D("20.00")
    assert q.discount == D("1.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("5.04")
    assert q.total == D("29.03")


@pytest.mark.ac("S6-AC1", "S6-AC2")
def test_vat_still_charged_on_shipping_when_fixed_coupon_empties_the_goods():
    # subtotal = 5.00; fixed coupon 10.00 is capped so goods never go below 0
    # discount = 5.00; goods after discount = 0.00 < 50 so shipping = 4.99
    # taxable = 0.00 + 4.99 = 4.99
    # tax = 4.99 * 0.21 = 1.0479 -> 1.05
    # total = 5.00 - 5.00 + 4.99 + 1.05 = 6.04
    coupon = Coupon("BIG", "fixed", D("10.00"))
    q = single("5.00", coupon=coupon)
    assert q.subtotal == D("5.00")
    assert q.discount == D("5.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("1.05")
    assert q.total == D("6.04")


# ------------------------------------------------------------- S6-AC2: rounding


@pytest.mark.ac("S6-AC2")
def test_tax_exactly_half_a_cent_rounds_up():
    # subtotal = 5.51, shipping = 4.99
    # taxable = 5.51 + 4.99 = 10.50
    # tax = 10.50 * 0.21 = 2.205 (exact tie) -> half up -> 2.21
    # total = 5.51 - 0.00 + 4.99 + 2.21 = 12.71
    q = single("5.51")
    assert q.tax == D("2.21")
    assert q.total == D("12.71")


@pytest.mark.ac("S6-AC2")
def test_tax_just_below_half_a_cent_rounds_down():
    # subtotal = 5.50, shipping = 4.99
    # taxable = 5.50 + 4.99 = 10.49
    # tax = 10.49 * 0.21 = 2.2029 -> 2.20
    # total = 5.50 - 0.00 + 4.99 + 2.20 = 12.69
    q = single("5.50")
    assert q.tax == D("2.20")
    assert q.total == D("12.69")


@pytest.mark.ac("S6-AC2")
def test_tax_just_above_half_a_cent_rounds_up():
    # subtotal = 5.52, shipping = 4.99
    # taxable = 5.52 + 4.99 = 10.51
    # tax = 10.51 * 0.21 = 2.2071 -> 2.21
    # total = 5.52 - 0.00 + 4.99 + 2.21 = 12.72
    q = single("5.52")
    assert q.tax == D("2.21")
    assert q.total == D("12.72")


@pytest.mark.ac("S6-AC2")
def test_subtotal_after_15_percent_volume_discount_rounds_half_up():
    # line = 1.01 * 50 = 50.50; 15% off -> 50.50 * 0.85 = 42.925 (tie)
    # subtotal -> half up -> 42.93
    # goods 42.93 < 50 so shipping = 4.99
    # taxable = 42.93 + 4.99 = 47.92
    # tax = 47.92 * 0.21 = 10.0632 -> 10.06
    # total = 42.93 - 0.00 + 4.99 + 10.06 = 57.98
    q = single("1.01", qty=50)
    assert q.subtotal == D("42.93")
    assert q.discount == D("0.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("10.06")
    assert q.total == D("57.98")


@pytest.mark.ac("S6-AC2")
def test_subtotal_after_10_percent_volume_discount_rounds_half_up():
    # line = 1.01 * 15 = 15.15; 10% off -> 15.15 * 0.90 = 13.635 (tie)
    # subtotal -> half up -> 13.64
    # goods 13.64 < 50 so shipping = 4.99
    # taxable = 13.64 + 4.99 = 18.63
    # tax = 18.63 * 0.21 = 3.9123 -> 3.91
    # total = 13.64 - 0.00 + 4.99 + 3.91 = 22.54
    q = single("1.01", qty=15)
    assert q.subtotal == D("13.64")
    assert q.tax == D("3.91")
    assert q.total == D("22.54")


@pytest.mark.ac("S6-AC2")
def test_loyalty_discount_rounds_half_up():
    # subtotal = 10.10; gold 5% -> 10.10 * 0.05 = 0.505 (tie) -> 0.51
    # goods = 10.10 - 0.51 = 9.59 < 50 so shipping = 4.99
    # taxable = 9.59 + 4.99 = 14.58
    # tax = 14.58 * 0.21 = 3.0618 -> 3.06
    # total = 10.10 - 0.51 + 4.99 + 3.06 = 17.64
    q = single("10.10", customer=Customer(tier="gold"))
    assert q.subtotal == D("10.10")
    assert q.discount == D("0.51")
    assert q.shipping == D("4.99")
    assert q.tax == D("3.06")
    assert q.total == D("17.64")


@pytest.mark.ac("S6-AC2")
def test_percent_coupon_discount_rounds_half_up():
    # subtotal = 10.05; coupon 10% -> 10.05 * 0.10 = 1.005 (tie) -> 1.01
    # goods = 10.05 - 1.01 = 9.04 < 50 so shipping = 4.99
    # taxable = 9.04 + 4.99 = 14.03
    # tax = 14.03 * 0.21 = 2.9463 -> 2.95
    # total = 10.05 - 1.01 + 4.99 + 2.95 = 16.98
    coupon = Coupon("SAVE10", "percent", D("10"))
    q = single("10.05", coupon=coupon)
    assert q.discount == D("1.01")
    assert q.shipping == D("4.99")
    assert q.tax == D("2.95")
    assert q.total == D("16.98")


@pytest.mark.ac("S6-AC2")
def test_discount_field_adds_rounded_loyalty_and_fixed_coupon():
    # subtotal = 10.10; gold 5% -> 0.505 -> 0.51
    # fixed coupon 1.00 taken off after loyalty
    # discount = 0.51 + 1.00 = 1.51
    # goods = 10.10 - 1.51 = 8.59 < 50 so shipping = 4.99
    # taxable = 8.59 + 4.99 = 13.58
    # tax = 13.58 * 0.21 = 2.8518 -> 2.85
    # total = 10.10 - 1.51 + 4.99 + 2.85 = 16.43
    coupon = Coupon("FIX", "fixed", D("1.00"))
    q = single("10.10", customer=Customer(tier="gold"), coupon=coupon)
    assert q.subtotal == D("10.10")
    assert q.discount == D("1.51")
    assert q.shipping == D("4.99")
    assert q.tax == D("2.85")
    assert q.total == D("16.43")


@pytest.mark.ac("S6-AC2", "S6-AC3")
def test_full_quote_with_volume_loyalty_and_fixed_coupon():
    # line = 20.00 * 10 = 200.00; 10% volume off -> 180.00 = subtotal
    # gold 5% -> 180.00 * 0.05 = 9.00; fixed coupon 5.00 after it
    # discount = 9.00 + 5.00 = 14.00
    # goods = 180.00 - 14.00 = 166.00 >= 50 so shipping = 0.00
    # taxable = 166.00 + 0.00 = 166.00
    # tax = 166.00 * 0.21 = 34.86
    # total = 180.00 - 14.00 + 0.00 + 34.86 = 200.86
    coupon = Coupon("FIX", "fixed", D("5.00"))
    q = single("20.00", qty=10, sku="VOL", customer=Customer(tier="gold"), coupon=coupon)
    assert q.subtotal == D("180.00")
    assert q.discount == D("14.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("34.86")
    assert q.total == D("200.86")
    assert q.applied == ("volume:VOL", "loyalty", "coupon:FIX")


# ---------------------------------------------------------------- S6-AC3: applied


@pytest.mark.ac("S6-AC3")
def test_applied_is_empty_when_nothing_applies():
    q = single("10.00")
    assert q.applied == ()


@pytest.mark.ac("S6-AC3")
def test_applied_lists_volume_skus_in_order_of_first_appearance_in_cart():
    # ZED appears before ALP in the cart (not alphabetical); ZED merges to 5 + 5 = 10
    cat = catalog_of(
        Product("ZED", "Zed", D("2.00")),
        Product("ALP", "Alp", D("2.00")),
    )
    lines = [Line("ZED", 5), Line("ALP", 10), Line("ZED", 5)]
    q = price_cart(lines, cat, today=TODAY)
    assert q.applied == ("volume:ZED", "volume:ALP")


@pytest.mark.ac("S6-AC3")
def test_applied_omits_products_without_volume_discount():
    cat = catalog_of(
        Product("BOOK", "Book", D("5.00"), category="books"),
        Product("GEN", "General", D("5.00")),
        Product("FEW", "Few", D("5.00")),
    )
    lines = [Line("BOOK", 20), Line("FEW", 9), Line("GEN", 10)]
    q = price_cart(lines, cat, today=TODAY)
    assert q.applied == ("volume:GEN",)


@pytest.mark.ac("S6-AC3")
def test_applied_lists_loyalty_after_volume_for_gold_customer():
    q = single("10.00", qty=10, sku="VOL", customer=Customer(tier="gold"))
    assert q.applied == ("volume:VOL", "loyalty")


@pytest.mark.ac("S6-AC3")
def test_applied_lists_coupon_when_percent_coupon_beats_loyalty():
    # coupon 10% > loyalty 5%
    coupon = Coupon("SAVE10", "percent", D("10"))
    q = single("10.00", qty=10, sku="VOL", customer=Customer(tier="gold"), coupon=coupon)
    assert q.applied == ("volume:VOL", "coupon:SAVE10")


@pytest.mark.ac("S6-AC3")
def test_applied_lists_loyalty_when_loyalty_beats_percent_coupon():
    # coupon 2% < loyalty 5%
    coupon = Coupon("SAVE2", "percent", D("2"))
    q = single("10.00", customer=Customer(tier="gold"), coupon=coupon)
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S6-AC3")
def test_applied_lists_coupon_not_loyalty_when_percentages_are_equal():
    # coupon 5% == loyalty 5%: the coupon wins
    coupon = Coupon("EQ5", "percent", D("5"))
    q = single("10.00", customer=Customer(tier="gold"), coupon=coupon)
    assert q.applied == ("coupon:EQ5",)


@pytest.mark.ac("S6-AC3")
def test_applied_lists_fixed_coupon_alone_for_standard_customer():
    coupon = Coupon("FIX", "fixed", D("1.00"))
    q = single("10.00", coupon=coupon)
    assert q.applied == ("coupon:FIX",)


@pytest.mark.ac("S6-AC3")
def test_applied_lists_fixed_coupon_after_loyalty():
    coupon = Coupon("FIX", "fixed", D("1.00"))
    q = single("10.00", customer=Customer(tier="gold"), coupon=coupon)
    assert q.applied == ("loyalty", "coupon:FIX")


@pytest.mark.ac("S6-AC3")
def test_applied_orders_volume_then_percent_coupon_for_multiple_products():
    cat = catalog_of(
        Product("ZED", "Zed", D("3.00")),
        Product("ALP", "Alp", D("3.00")),
    )
    lines = [Line("ZED", 10), Line("ALP", 50)]
    coupon = Coupon("SAVE10", "percent", D("10"))
    q = price_cart(lines, cat, today=TODAY, customer=Customer(tier="gold"), coupon=coupon)
    assert q.applied == ("volume:ZED", "volume:ALP", "coupon:SAVE10")
