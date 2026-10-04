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

STANDARD_FEE = Decimal("4.99")
EXPRESS_FEE = Decimal("9.99")
ZERO = Decimal("0.00")


def _catalog(price, sku="A", category="general"):
    return {sku: Product(sku=sku, name="Item " + sku, unit_price=Decimal(price), category=category)}


def _quote(price, qty=1, **kwargs):
    return price_cart(
        [Line("A", qty)],
        _catalog(price),
        today=TODAY,
        **kwargs,
    )


# ---------------------------------------------------------------- S5-AC1

@pytest.mark.ac("S5-AC1")
def test_standard_shipping_is_charged_on_small_order():
    # goods = 10.00 < 50.00 -> shipping 4.99
    q = _quote("10.00")
    assert q.shipping == Decimal("4.99")


@pytest.mark.ac("S5-AC1")
def test_standard_is_default_shipping_method():
    # No shipping argument: default "standard". goods = 10.00 -> 4.99
    q = _quote("10.00")
    explicit = _quote("10.00", shipping="standard")
    assert q.shipping == Decimal("4.99")
    assert explicit.shipping == Decimal("4.99")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_charged_just_below_free_threshold():
    # goods = 49.99 < 50.00 -> shipping 4.99
    q = _quote("49.99")
    assert q.shipping == Decimal("4.99")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_exactly_at_threshold():
    # goods = 50.00 >= 50.00 -> shipping 0.00
    q = _quote("50.00")
    assert q.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_just_above_threshold():
    # goods = 50.01 >= 50.00 -> shipping 0.00
    q = _quote("50.01")
    assert q.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_on_large_order():
    # goods = 2 * 100.00 = 200.00 -> shipping 0.00
    q = _quote("100.00", qty=2)
    assert q.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC1")
def test_free_shipping_threshold_uses_goods_after_fixed_coupon_at_boundary():
    # subtotal = 60.00; fixed coupon 10.00 -> goods = 50.00 -> free
    coupon = Coupon(code="F10", kind="fixed", value=Decimal("10.00"))
    q = _quote("60.00", coupon=coupon)
    assert q.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC1")
def test_shipping_charged_when_fixed_coupon_brings_goods_just_below_threshold():
    # subtotal = 60.00; fixed coupon 10.01 -> goods = 49.99 < 50.00 -> 4.99
    coupon = Coupon(code="F1001", kind="fixed", value=Decimal("10.01"))
    q = _quote("60.00", coupon=coupon)
    assert q.shipping == Decimal("4.99")


@pytest.mark.ac("S5-AC1")
def test_shipping_charged_when_fixed_coupon_drops_goods_below_threshold():
    # subtotal = 60.00; fixed coupon 11.00 -> goods = 49.00 < 50.00 -> 4.99
    coupon = Coupon(code="F11", kind="fixed", value=Decimal("11.00"))
    q = _quote("60.00", coupon=coupon)
    assert q.shipping == Decimal("4.99")


@pytest.mark.ac("S5-AC1")
def test_free_shipping_threshold_uses_goods_after_percent_coupon_at_boundary():
    # subtotal = 100.00; 50% coupon -> discount 50.00 -> goods = 50.00 -> free
    coupon = Coupon(code="HALF", kind="percent", value=Decimal("50"))
    q = _quote("100.00", coupon=coupon)
    assert q.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC1")
def test_shipping_charged_when_percent_coupon_drops_goods_below_threshold():
    # subtotal = 100.00; 51% coupon -> discount 51.00 -> goods = 49.00 < 50.00 -> 4.99
    coupon = Coupon(code="P51", kind="percent", value=Decimal("51"))
    q = _quote("100.00", coupon=coupon)
    assert q.shipping == Decimal("4.99")


@pytest.mark.ac("S5-AC1")
def test_shipping_charged_when_fixed_coupon_zeroes_the_goods():
    # subtotal = 30.00; fixed 100.00 coupon, goods floored at 0.00 -> 4.99
    coupon = Coupon(code="BIG", kind="fixed", value=Decimal("100.00"))
    q = _quote("30.00", coupon=coupon)
    assert q.shipping == Decimal("4.99")


@pytest.mark.ac("S5-AC1")
def test_free_shipping_threshold_uses_goods_after_loyalty_discount_below():
    # subtotal = 52.00; gold 5% = 2.60 -> goods = 49.40 < 50.00 -> 4.99
    q = _quote("52.00", customer=Customer(tier="gold"))
    assert q.shipping == Decimal("4.99")


@pytest.mark.ac("S5-AC1")
def test_free_shipping_threshold_uses_goods_after_loyalty_discount_at_boundary():
    # subtotal = 52.63; gold 5% = 2.6315 -> rounded 2.63
    # goods = 52.63 - 2.63 = 50.00 -> free
    q = _quote("52.63", customer=Customer(tier="gold"))
    assert q.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_customer_with_same_cart_as_gold_gets_free_shipping():
    # subtotal = 52.00; standard tier, no discount -> goods = 52.00 >= 50.00 -> free
    q = _quote("52.00", customer=Customer(tier="standard"))
    assert q.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC1")
def test_shipping_charged_when_volume_discount_drops_goods_below_threshold():
    # 10 units * 5.50 = 55.00; volume 10% off -> 49.50 < 50.00 -> 4.99
    q = _quote("5.50", qty=10)
    assert q.shipping == Decimal("4.99")


@pytest.mark.ac("S5-AC1")
def test_free_shipping_when_goods_after_volume_discount_reach_threshold():
    # 10 units * 5.60 = 56.00; volume 10% off -> 50.40 >= 50.00 -> free
    q = _quote("5.60", qty=10)
    assert q.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC1")
def test_free_shipping_threshold_counts_goods_not_shipping_fee():
    # goods = 45.10 (+4.99 fee would be 50.09, but fee is not goods) -> still charged
    q = _quote("45.10")
    assert q.shipping == Decimal("4.99")


# ---------------------------------------------------------------- S5-AC2

@pytest.mark.ac("S5-AC2")
def test_express_shipping_costs_9_99_on_small_order():
    # goods = 10.00 -> express 9.99
    q = _quote("10.00", shipping="express")
    assert q.shipping == Decimal("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_not_free_exactly_at_free_threshold():
    # goods = 50.00 -> standard would be free, express still 9.99
    q = _quote("50.00", shipping="express")
    assert q.shipping == Decimal("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_not_free_just_above_free_threshold():
    # goods = 50.01 -> express still 9.99
    q = _quote("50.01", shipping="express")
    assert q.shipping == Decimal("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_not_free_on_large_order():
    # goods = 5 * 100.00 = 500.00 -> express still 9.99
    q = _quote("100.00", qty=5, shipping="express")
    assert q.shipping == Decimal("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_charged_just_below_threshold():
    # goods = 49.99 -> express 9.99
    q = _quote("49.99", shipping="express")
    assert q.shipping == Decimal("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_charged_when_goods_are_zero_after_coupon():
    # subtotal = 30.00; fixed 100.00 coupon -> goods 0.00; express 9.99
    coupon = Coupon(code="BIG", kind="fixed", value=Decimal("100.00"))
    q = _quote("30.00", shipping="express", coupon=coupon)
    assert q.shipping == Decimal("9.99")


# ------------------------------------------------------- S5-AC1 / S5-AC2 in quote

@pytest.mark.ac("S5-AC1")
def test_quote_total_with_paid_standard_shipping():
    # subtotal = 20.00, discount = 0.00, shipping = 4.99
    # tax = 21% * (20.00 + 4.99) = 0.21 * 24.99 = 5.2479 -> 5.25
    # total = 20.00 - 0.00 + 4.99 + 5.25 = 30.24
    q = _quote("20.00")
    assert q.subtotal == Decimal("20.00")
    assert q.shipping == Decimal("4.99")
    assert q.tax == Decimal("5.25")
    assert q.total == Decimal("30.24")


@pytest.mark.ac("S5-AC1")
def test_quote_total_with_free_standard_shipping():
    # subtotal = 60.00, discount = 0.00, shipping = 0.00
    # tax = 0.21 * (60.00 + 0.00) = 12.60
    # total = 60.00 + 0.00 + 12.60 = 72.60
    q = _quote("60.00")
    assert q.shipping == Decimal("0.00")
    assert q.tax == Decimal("12.60")
    assert q.total == Decimal("72.60")


@pytest.mark.ac("S5-AC2")
def test_quote_total_with_express_shipping_on_large_order():
    # subtotal = 60.00, discount = 0.00, shipping = 9.99
    # tax = 0.21 * (60.00 + 9.99) = 0.21 * 69.99 = 14.6979 -> 14.70
    # total = 60.00 + 9.99 + 14.70 = 84.69
    q = _quote("60.00", shipping="express")
    assert q.shipping == Decimal("9.99")
    assert q.tax == Decimal("14.70")
    assert q.total == Decimal("84.69")


# ---------------------------------------------------------------- S5-AC3

@pytest.mark.ac("S5-AC3")
def test_unknown_shipping_method_raises_cart_error():
    with pytest.raises(CartError):
        _quote("10.00", shipping="overnight")


@pytest.mark.ac("S5-AC3")
def test_empty_string_shipping_method_raises_cart_error():
    with pytest.raises(CartError):
        _quote("10.00", shipping="")


@pytest.mark.ac("S5-AC3")
def test_pickup_shipping_method_raises_cart_error():
    with pytest.raises(CartError):
        _quote("10.00", shipping="pickup")


@pytest.mark.ac("S5-AC3")
def test_invalid_shipping_method_raises_cart_error_even_on_free_shipping_order():
    # goods = 100.00 would be free for standard, but "overnight" is not a method
    with pytest.raises(CartError):
        _quote("100.00", shipping="overnight")
```