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

CATALOG = {
    "A": Product("A", "Alpha", D("10.00")),
    "B": Product("B", "Beta", D("20.00")),
    "C": Product("C", "Gamma", D("5.00")),
    "BK": Product("BK", "Book", D("12.00"), "books"),
}


def single(price, category="general", sku="X"):
    return {sku: Product(sku, "Thing", D(price), category)}


def quote(lines, catalog, **kw):
    return price_cart(lines, catalog, today=TODAY, **kw)


def pct(code, value):
    return Coupon(code, "percent", D(str(value)))


def fixed(code, value):
    return Coupon(code, "fixed", D(str(value)))


GOLD = Customer(tier="gold")


# --------------------------------------------------------------------------
# S6-AC1: VAT is 21% of goods after discounts plus shipping
# --------------------------------------------------------------------------

@pytest.mark.ac("S6-AC1")
def test_vat_on_goods_with_free_shipping():
    q = quote([Line("X", 1)], single("100.00"))
    assert q.subtotal == D("100.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("21.00")
    assert q.total == D("121.00")


@pytest.mark.ac("S6-AC1")
def test_vat_includes_standard_shipping():
    q = quote([Line("X", 1)], single("20.00"))
    assert q.shipping == D("4.99")
    assert q.tax == D("5.25")
    assert q.total == D("30.24")


@pytest.mark.ac("S6-AC1")
def test_vat_includes_express_shipping():
    q = quote([Line("X", 1)], single("100.00"), shipping="express")
    assert q.shipping == D("9.99")
    assert q.tax == D("23.10")
    assert q.total == D("133.09")


@pytest.mark.ac("S6-AC1")
def test_vat_is_taken_after_percent_coupon():
    q = quote([Line("X", 1)], single("100.00"), coupon=pct("SAVE10", 10))
    assert q.discount == D("10.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")


@pytest.mark.ac("S6-AC1")
def test_vat_is_taken_after_loyalty_discount():
    q = quote([Line("X", 1)], single("100.00"), customer=GOLD)
    assert q.discount == D("5.00")
    assert q.tax == D("19.95")
    assert q.total == D("114.95")


@pytest.mark.ac("S6-AC1")
def test_vat_is_taken_after_fixed_coupon():
    q = quote([Line("X", 1)], single("100.00"), coupon=fixed("MINUS15", 15))
    assert q.discount == D("15.00")
    assert q.tax == D("17.85")
    assert q.total == D("102.85")


@pytest.mark.ac("S6-AC1")
def test_vat_is_taken_after_volume_discount():
    q = quote([Line("A", 10)], CATALOG)
    assert q.subtotal == D("90.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")


@pytest.mark.ac("S6-AC1")
def test_vat_on_books_is_also_21_percent():
    q = quote([Line("X", 1)], single("100.00", category="books"))
    assert q.tax == D("21.00")
    assert q.total == D("121.00")


@pytest.mark.ac("S6-AC1", "S6-AC2")
def test_vat_covers_shipping_when_discount_drops_goods_below_free_threshold():
    q = quote([Line("X", 1)], single("55.00"), coupon=pct("SAVE10", 10))
    assert q.subtotal == D("55.00")
    assert q.discount == D("5.50")
    assert q.shipping == D("4.99")
    assert q.tax == D("11.44")
    assert q.total == D("65.93")


@pytest.mark.ac("S6-AC1", "S6-AC2")
def test_fixed_coupon_larger_than_goods_leaves_vat_on_shipping_only():
    q = quote([Line("X", 1)], single("10.00"), coupon=fixed("BIG", 20))
    assert q.discount == D("10.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("1.05")
    assert q.total == D("6.04")


# --------------------------------------------------------------------------
# S6-AC2: rounding half up to the cent, total is exact sum
# --------------------------------------------------------------------------

@pytest.mark.ac("S6-AC2")
def test_tax_rounds_half_up_with_express_shipping():
    # goods 10.51 + 9.99 = 20.50 -> tax 4.305 -> 4.31
    q = quote([Line("X", 1)], single("10.51"), shipping="express")
    assert q.tax == D("4.31")
    assert q.total == D("24.81")


@pytest.mark.ac("S6-AC2")
def test_tax_rounds_half_up_with_free_shipping():
    # goods 50.50 -> tax 10.605 -> 10.61
    q = quote([Line("X", 1)], single("50.50"))
    assert q.shipping == D("0.00")
    assert q.tax == D("10.61")
    assert q.total == D("61.11")


@pytest.mark.ac("S6-AC2")
def test_percent_coupon_discount_rounds_half_up():
    # 10% of 10.05 = 1.005 -> 1.01
    q = quote([Line("X", 1)], single("10.05"), coupon=pct("SAVE10", 10))
    assert q.subtotal == D("10.05")
    assert q.discount == D("1.01")
    assert q.shipping == D("4.99")
    assert q.tax == D("2.95")
    assert q.total == D("16.98")


@pytest.mark.ac("S6-AC2")
def test_loyalty_discount_rounds_half_up():
    # 5% of 10.10 = 0.505 -> 0.51
    q = quote([Line("X", 1)], single("10.10"), customer=GOLD)
    assert q.discount == D("0.51")
    assert q.tax == D("3.06")
    assert q.total == D("17.64")


@pytest.mark.ac("S6-AC2")
def test_loyalty_and_fixed_coupon_discounts_are_summed():
    q = quote(
        [Line("X", 1)],
        single("10.10"),
        customer=GOLD,
        coupon=fixed("ONE", 1),
    )
    assert q.discount == D("1.51")
    assert q.shipping == D("4.99")
    assert q.tax == D("2.85")
    assert q.total == D("16.43")


@pytest.mark.ac("S6-AC2")
def test_subtotal_rounds_half_up_after_15_percent_volume_discount():
    # 50 x 0.01 = 0.50, minus 15% = 0.425 -> 0.43
    q = quote([Line("X", 50)], single("0.01"))
    assert q.subtotal == D("0.43")
    assert q.shipping == D("4.99")
    assert q.tax == D("1.14")
    assert q.total == D("6.56")


@pytest.mark.ac("S6-AC2")
def test_subtotal_rounds_half_up_after_10_percent_volume_discount():
    # 11 x 0.05 = 0.55, minus 10% = 0.495 -> 0.50
    q = quote([Line("X", 11)], single("0.05"))
    assert q.subtotal == D("0.50")
    assert q.shipping == D("4.99")
    assert q.tax == D("1.15")
    assert q.total == D("6.64")


SCENARIOS = [
    dict(lines=[Line("X", 1)], price="19.99", kw={}),
    dict(lines=[Line("X", 3)], price="33.33", kw={}),
    dict(lines=[Line("X", 7)], price="3.17", kw=dict(customer=GOLD)),
    dict(lines=[Line("X", 12)], price="4.37", kw=dict(coupon=pct("P7", 7))),
    dict(lines=[Line("X", 60)], price="1.23", kw=dict(shipping="express")),
    dict(
        lines=[Line("X", 13)],
        price="7.77",
        kw=dict(customer=GOLD, coupon=fixed("F", "2.50")),
    ),
    dict(lines=[Line("X", 1)], price="10.05", kw=dict(coupon=pct("P10", 10))),
    dict(lines=[Line("X", 1)], price="0.99", kw=dict(coupon=fixed("F", 5))),
    dict(lines=[Line("X", 99)], price="12.34", kw=dict(customer=GOLD)),
]


@pytest.mark.ac("S6-AC2")
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_total_is_exactly_subtotal_minus_discount_plus_shipping_plus_tax(scenario):
    q = quote(scenario["lines"], single(scenario["price"]), **scenario["kw"])
    assert q.total == q.subtotal - q.discount + q.shipping + q.tax


@pytest.mark.ac("S6-AC2")
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_every_amount_is_a_whole_number_of_cents(scenario):
    q = quote(scenario["lines"], single(scenario["price"]), **scenario["kw"])
    cent = D("0.01")
    for amount in (q.subtotal, q.discount, q.shipping, q.tax, q.total):
        assert amount == amount.quantize(cent)


# --------------------------------------------------------------------------
# S6-AC3: order and content of `applied`
# --------------------------------------------------------------------------

@pytest.mark.ac("S6-AC3")
def test_nothing_applied_gives_empty_tuple():
    q = quote([Line("A", 1)], CATALOG)
    assert q.applied == ()


@pytest.mark.ac("S6-AC3")
def test_volume_entries_follow_first_appearance_in_cart():
    lines = [Line("B", 10), Line("C", 1), Line("A", 10)]
    q = quote(lines, CATALOG)
    assert q.applied == ("volume:B", "volume:A")


@pytest.mark.ac("S6-AC3")
def test_volume_order_uses_first_appearance_when_lines_are_merged():
    lines = [Line("A", 5), Line("B", 10), Line("A", 5)]
    q = quote(lines, CATALOG)
    assert q.applied == ("volume:A", "volume:B")


@pytest.mark.ac("S6-AC3")
def test_products_without_volume_discount_are_not_listed():
    lines = [Line("C", 9), Line("BK", 60), Line("A", 10)]
    q = quote(lines, CATALOG)
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S6-AC3")
def test_volume_applies_once_per_product_for_15_percent_tier():
    q = quote([Line("A", 50)], CATALOG)
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S6-AC3")
def test_loyalty_is_listed_for_gold_customer():
    q = quote([Line("A", 1)], CATALOG, customer=GOLD)
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S6-AC3")
def test_standard_customer_has_no_loyalty_entry():
    q = quote([Line("A", 1)], CATALOG, customer=Customer(tier="standard"))
    assert "loyalty" not in q.applied


@pytest.mark.ac("S6-AC3")
def test_percent_coupon_listed_alone():
    q = quote([Line("A", 1)], CATALOG, coupon=pct("SAVE10", 10))
    assert q.applied == ("coupon:SAVE10",)


@pytest.mark.ac("S6-AC3")
def test_larger_percent_coupon_replaces_loyalty_entry():
    q = quote([Line("A", 1)], CATALOG, customer=GOLD, coupon=pct("SAVE10", 10))
    assert q.applied == ("coupon:SAVE10",)


@pytest.mark.ac("S6-AC3")
def test_larger_loyalty_replaces_percent_coupon_entry():
    q = quote([Line("A", 1)], CATALOG, customer=GOLD, coupon=pct("SAVE3", 3))
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S6-AC3")
def test_equal_loyalty_and_percent_coupon_lists_the_coupon():
    q = quote([Line("A", 1)], CATALOG, customer=GOLD, coupon=pct("FIVE", 5))
    assert q.applied == ("coupon:FIVE",)


@pytest.mark.ac("S6-AC3")
def test_fixed_coupon_listed_alone():
    q = quote([Line("A", 1)], CATALOG, coupon=fixed("FIX5", 5))
    assert q.applied == ("coupon:FIX5",)


@pytest.mark.ac("S6-AC3")
def test_fixed_coupon_comes_after_loyalty():
    q = quote([Line("A", 1)], CATALOG, customer=GOLD, coupon=fixed("FIX5", 5))
    assert q.applied == ("loyalty", "coupon:FIX5")


@pytest.mark.ac("S6-AC3")
def test_full_order_volume_then_loyalty_then_fixed_coupon():
    lines = [Line("C", 1), Line("B", 10), Line("A", 10)]
    q = quote(lines, CATALOG, customer=GOLD, coupon=fixed("FIX5", 5))
    assert q.applied == ("volume:B", "volume:A", "loyalty", "coupon:FIX5")


@pytest.mark.ac("S6-AC3")
def test_volume_entries_come_before_percent_coupon():
    lines = [Line("C", 1), Line("B", 10)]
    q = quote(lines, CATALOG, customer=GOLD, coupon=pct("BIG", 20))
    assert q.applied == ("volume:B", "coupon:BIG")


@pytest.mark.ac("S6-AC3")
def test_applied_is_a_tuple_of_strings():
    q = quote([Line("A", 10)], CATALOG, customer=GOLD, coupon=fixed("F", 1))
    assert isinstance(q.applied, tuple)
    assert all(isinstance(item, str) for item in q.applied)
