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


def catalog(*products):
    return {p.sku: p for p in products}


def cart_of_price(price, qty=1, category="general"):
    cat = catalog(Product("A", "Item A", D(price), category))
    return [Line("A", qty)], cat


def ship(price, qty=1, **kwargs):
    lines, cat = cart_of_price(price, qty)
    return price_cart(lines, cat, today=TODAY, **kwargs)


# ---------- S5-AC1: standard shipping ----------

@pytest.mark.ac("S5-AC1")
def test_standard_shipping_charged_on_small_order():
    q = ship("10.00", shipping="standard")
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_standard_is_default_shipping_method():
    q = ship("10.00")
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_charged_just_below_threshold():
    q = ship("49.99", shipping="standard")
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_at_exact_threshold():
    q = ship("50.00", shipping="standard")
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_above_threshold():
    q = ship("120.00", shipping="standard")
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_from_multiple_lines_adding_up():
    cat = catalog(Product("A", "A", D("30.00")), Product("B", "B", D("20.00")))
    q = price_cart([Line("A", 1), Line("B", 1)], cat, today=TODAY)
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_for_books_category():
    lines, cat = cart_of_price("50.00", category="books")
    q = price_cart(lines, cat, today=TODAY)
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_charged_quote_totals():
    q = ship("10.00")
    # tax = 21% of (10.00 + 4.99) = 3.1479 -> 3.15
    assert q.subtotal == D("10.00")
    assert q.tax == D("3.15")
    assert q.total == D("18.14")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_quote_totals():
    q = ship("50.00")
    assert q.tax == D("10.50")
    assert q.total == D("60.50")


# ---------- S5-AC1: threshold uses goods after all discounts ----------

@pytest.mark.ac("S5-AC1")
def test_fixed_coupon_bringing_goods_to_exactly_threshold_keeps_free_shipping():
    coupon = Coupon("FIVE", "fixed", D("5.00"))
    q = ship("55.00", coupon=coupon)
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_fixed_coupon_bringing_goods_below_threshold_charges_shipping():
    coupon = Coupon("FIVE1", "fixed", D("5.01"))
    q = ship("55.00", coupon=coupon)
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_percent_coupon_bringing_goods_below_threshold_charges_shipping():
    coupon = Coupon("SAVE10", "percent", D("10"))
    q = ship("55.00", coupon=coupon)  # 55.00 - 5.50 = 49.50
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_percent_coupon_keeping_goods_above_threshold_is_free():
    coupon = Coupon("SAVE10", "percent", D("10"))
    q = ship("60.00", coupon=coupon)  # 54.00
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_percent_coupon_on_exactly_threshold_order_charges_shipping():
    coupon = Coupon("SAVE10", "percent", D("10"))
    q = ship("50.00", coupon=coupon)  # 45.00
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_loyalty_discount_bringing_goods_below_threshold_charges_shipping():
    q = ship("52.00", customer=Customer(tier="gold"))  # 52.00 - 2.60 = 49.40
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_loyalty_discount_keeping_goods_above_threshold_is_free():
    q = ship("53.00", customer=Customer(tier="gold"))  # 53.00 - 2.65 = 50.35
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_loyalty_plus_fixed_coupon_exactly_at_threshold_is_free():
    coupon = Coupon("SEVEN", "fixed", D("7.00"))
    q = ship("60.00", customer=Customer(tier="gold"), coupon=coupon)  # 57 - 7 = 50
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_loyalty_plus_fixed_coupon_just_below_threshold_charges_shipping():
    coupon = Coupon("SEVEN01", "fixed", D("7.01"))
    q = ship("60.00", customer=Customer(tier="gold"), coupon=coupon)  # 49.99
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_volume_discount_bringing_goods_below_threshold_charges_shipping():
    q = ship("5.50", qty=10)  # 55.00 - 10% = 49.50
    assert q.shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_volume_discount_keeping_goods_above_threshold_is_free():
    q = ship("5.60", qty=10)  # 56.00 - 10% = 50.40
    assert q.shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_fixed_coupon_larger_than_goods_charges_shipping():
    coupon = Coupon("BIG", "fixed", D("100.00"))
    q = ship("20.00", coupon=coupon)
    assert q.shipping == D("4.99")


# ---------- S5-AC2: express shipping ----------

@pytest.mark.ac("S5-AC2")
def test_express_shipping_costs_9_99_on_small_order():
    q = ship("10.00", shipping="express")
    assert q.shipping == D("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_not_free_at_threshold():
    q = ship("50.00", shipping="express")
    assert q.shipping == D("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_not_free_on_large_order():
    q = ship("500.00", shipping="express")
    assert q.shipping == D("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_not_free_with_discounts_above_threshold():
    coupon = Coupon("SAVE10", "percent", D("10"))
    q = ship("100.00", shipping="express", coupon=coupon,
             customer=Customer(tier="gold"))
    assert q.shipping == D("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_quote_totals():
    q = ship("10.00", shipping="express")
    # tax = 21% of (10.00 + 9.99) = 4.1979 -> 4.20
    assert q.tax == D("4.20")
    assert q.total == D("24.19")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_quote_totals_on_large_order():
    q = ship("100.00", shipping="express")
    # tax = 21% of (100.00 + 9.99) = 23.0979 -> 23.10
    assert q.tax == D("23.10")
    assert q.total == D("133.09")


# ---------- S5-AC3: unknown shipping methods ----------

@pytest.mark.ac("S5-AC3")
@pytest.mark.parametrize("method", ["overnight", "pickup", "free", "", "drone"])
def test_unknown_shipping_method_raises_cart_error(method):
    with pytest.raises(CartError):
        ship("10.00", shipping=method)


@pytest.mark.ac("S5-AC3")
def test_unknown_shipping_method_raises_even_when_order_would_ship_free():
    with pytest.raises(CartError):
        ship("100.00", shipping="overnight")


@pytest.mark.ac("S5-AC3")
def test_unknown_shipping_method_raises_with_coupon_and_loyalty():
    coupon = Coupon("SAVE10", "percent", D("10"))
    with pytest.raises(CartError):
        ship("100.00", shipping="pickup", coupon=coupon,
             customer=Customer(tier="gold"))
```