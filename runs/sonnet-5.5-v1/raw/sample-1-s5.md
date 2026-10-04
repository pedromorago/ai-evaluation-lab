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
D = Decimal


def catalog_for(price, category="general"):
    return {"A": Product(sku="A", name="Item A", unit_price=D(price), category=category)}


def quote(price, qty=1, **kwargs):
    return price_cart([Line("A", qty)], catalog_for(price), today=TODAY, **kwargs)


# ---------------------------------------------------------------- S5-AC1

@pytest.mark.ac("S5-AC1")
def test_standard_shipping_costs_4_99_on_small_order():
    q = quote("10.00")
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_standard_is_the_default_shipping_method():
    default = quote("10.00")
    explicit = quote("10.00", shipping="standard")
    assert default.shipping == explicit.shipping == D("4.99")
    assert default.total == explicit.total


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_just_below_threshold_is_charged():
    q = quote("49.99")
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_at_exactly_50():
    q = quote("50.00")
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_just_above_threshold():
    q = quote("50.01")
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_on_large_order():
    q = quote("500.00")
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_free_threshold_reached_with_multiple_units():
    q = quote("25.00", qty=2)
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_free_threshold_reached_across_several_products():
    catalog = {
        "A": Product("A", "A", D("30.00")),
        "B": Product("B", "B", D("20.00")),
    }
    q = price_cart([Line("A", 1), Line("B", 1)], catalog, today=TODAY)
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_below_threshold_across_several_products_is_charged():
    catalog = {
        "A": Product("A", "A", D("30.00")),
        "B": Product("B", "B", D("19.99")),
    }
    q = price_cart([Line("A", 1), Line("B", 1)], catalog, today=TODAY)
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_charged_shipping_flows_into_tax_and_total():
    # goods 10.00 + shipping 4.99 = 14.99; VAT 21% = 3.1479 -> 3.15
    q = quote("10.00")
    assert q.subtotal == D("10.00")
    assert q.discount == D("0.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("3.15")
    assert q.total == D("18.14")


@pytest.mark.ac("S5-AC1")
def test_free_shipping_flows_into_tax_and_total():
    # goods 50.00, no shipping; VAT 10.50
    q = quote("50.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("10.50")
    assert q.total == D("60.50")


@pytest.mark.ac("S5-AC1")
def test_percent_coupon_dropping_goods_below_50_makes_shipping_charged():
    # 55.00 - 10% = 49.50 -> below threshold
    q = quote("55.00", coupon=Coupon("SAVE10", "percent", D("10")))
    assert q.shipping == D("4.99")
    assert q.total == q.subtotal - q.discount + q.shipping + q.tax


@pytest.mark.ac("S5-AC1")
def test_percent_coupon_leaving_goods_at_exactly_50_is_free():
    # 100.00 - 50% = 50.00
    q = quote("100.00", coupon=Coupon("HALF", "percent", D("50")))
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_percent_coupon_leaving_goods_above_50_is_free():
    # 100.00 - 10% = 90.00
    q = quote("100.00", coupon=Coupon("SAVE10", "percent", D("10")))
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_fixed_coupon_leaving_goods_at_exactly_50_is_free():
    q = quote("60.00", coupon=Coupon("TEN", "fixed", D("10.00")))
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_fixed_coupon_dropping_goods_just_below_50_is_charged():
    q = quote("60.00", coupon=Coupon("TEN01", "fixed", D("10.01")))
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_fixed_coupon_larger_than_goods_leaves_shipping_charged():
    q = quote("20.00", coupon=Coupon("BIG", "fixed", D("100.00")))
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_gold_loyalty_discount_dropping_goods_below_50_is_charged():
    # 52.00 - 5% (2.60) = 49.40
    q = quote("52.00", customer=Customer(tier="gold"))
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_gold_customer_with_large_order_gets_free_shipping():
    q = quote("100.00", customer=Customer(tier="gold"))
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_tier_at_52_is_free_but_gold_is_not():
    standard = quote("52.00", customer=Customer(tier="standard"))
    gold = quote("52.00", customer=Customer(tier="gold"))
    assert standard.shipping == D("0.00")
    assert gold.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_volume_discount_dropping_goods_below_50_is_charged():
    # 10 x 5.50 = 55.00, minus 10% = 49.50
    q = quote("5.50", qty=10)
    assert q.subtotal == D("49.50")
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_volume_discount_leaving_goods_above_50_is_free():
    # 10 x 5.56 = 55.60, minus 10% = 50.04
    q = quote("5.56", qty=10)
    assert q.subtotal == D("50.04")
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_books_without_volume_discount_free_at_threshold():
    # books never get volume discount: 10 x 5.50 = 55.00 stays 55.00
    cat = catalog_for("5.50", category="books")
    q = price_cart([Line("A", 10)], cat, today=TODAY)
    assert q.subtotal == D("55.00")
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_gold_with_percent_coupon_uses_goods_after_the_winning_discount():
    # 55.00; coupon 20% (11.00) beats loyalty 5% -> goods 44.00
    q = quote(
        "55.00",
        customer=Customer(tier="gold"),
        coupon=Coupon("TWENTY", "percent", D("20")),
    )
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_gold_with_fixed_coupon_uses_goods_after_both_discounts():
    # 60.00 - 5% (3.00) - 7.00 = 50.00 -> free
    q = quote(
        "60.00",
        customer=Customer(tier="gold"),
        coupon=Coupon("SEVEN", "fixed", D("7.00")),
    )
    assert q.shipping == D("0.00")
    # 60.00 - 3.00 - 7.01 = 49.99 -> charged
    q2 = quote(
        "60.00",
        customer=Customer(tier="gold"),
        coupon=Coupon("SEVEN01", "fixed", D("7.01")),
    )
    assert q2.shipping == D("4.99")


# ---------------------------------------------------------------- S5-AC2

@pytest.mark.ac("S5-AC2")
def test_express_shipping_costs_9_99_on_small_order():
    q = quote("10.00", shipping="express")
    assert q.shipping == D("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_not_free_at_threshold():
    q = quote("50.00", shipping="express")
    assert q.shipping == D("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_not_free_on_large_order():
    q = quote("1000.00", shipping="express")
    assert q.shipping == D("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_not_free_with_discounts_and_large_goods():
    q = quote(
        "99.00",
        qty=10,
        customer=Customer(tier="gold"),
        coupon=Coupon("SAVE10", "percent", D("10")),
        shipping="express",
    )
    assert q.shipping == D("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_flows_into_tax_and_total():
    # goods 100.00 + 9.99 = 109.99; VAT 21% = 23.0979 -> 23.10
    q = quote("100.00", shipping="express")
    assert q.shipping == D("9.99")
    assert q.tax == D("23.10")
    assert q.total == D("133.09")


@pytest.mark.ac("S5-AC2")
def test_express_small_order_tax_and_total():
    # goods 10.00 + 9.99 = 19.99; VAT = 4.1979 -> 4.20
    q = quote("10.00", shipping="express")
    assert q.tax == D("4.20")
    assert q.total == D("24.19")


@pytest.mark.ac("S5-AC2")
def test_express_costs_more_than_standard_on_small_order():
    std = quote("10.00", shipping="standard")
    exp = quote("10.00", shipping="express")
    assert exp.shipping - std.shipping == D("5.00")


# ---------------------------------------------------------------- S5-AC3

@pytest.mark.ac("S5-AC3")
@pytest.mark.parametrize("method", ["overnight", "pickup", "", "free", "fast"])
def test_unknown_shipping_method_raises_cart_error(method):
    with pytest.raises(CartError):
        quote("10.00", shipping=method)


@pytest.mark.ac("S5-AC3")
def test_unknown_shipping_method_raises_even_on_large_order():
    with pytest.raises(CartError):
        quote("500.00", shipping="overnight")


@pytest.mark.ac("S5-AC3")
def test_unknown_shipping_method_raises_with_discounts_applied():
    with pytest.raises(CartError):
        quote(
            "100.00",
            customer=Customer(tier="gold"),
            coupon=Coupon("SAVE10", "percent", D("10")),
            shipping="drone",
        )
```