```python
import pytest
from decimal import Decimal
from datetime import date
from checkout import Product, Line, Customer, Coupon, price_cart, CartError


# S5-AC1: Standard shipping costs 4.99, free when goods >= 50.00 after all discounts

@pytest.mark.ac("S5-AC1")
def test_standard_shipping_4_99_when_goods_below_50():
    """Standard shipping costs 4.99 when goods after discounts are below 50.00"""
    # Subtotal: 49.99, no discounts
    # Goods after discounts: 49.99 < 50.00
    # Shipping: 4.99
    # Tax: 21% of (49.99 + 4.99) = 11.5458 → 11.55
    # Total: 49.99 + 4.99 + 11.55 = 66.53
    catalog = {"ITEM1": Product("ITEM1", "Item", Decimal("49.99"))}
    quote = price_cart(
        [Line("ITEM1", 1)],
        catalog,
        today=date(2026, 1, 1),
        shipping="standard"
    )
    assert quote.shipping == Decimal("4.99")
    assert quote.total == Decimal("66.53")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_at_exactly_50():
    """Standard shipping is free when goods after discounts equal 50.00"""
    # Subtotal: 50.00, no discounts
    # Goods after discounts: 50.00
    # Shipping: 0.00
    # Tax: 21% of 50.00 = 10.50
    # Total: 50.00 + 0.00 + 10.50 = 60.50
    catalog = {"ITEM1": Product("ITEM1", "Item", Decimal("50.00"))}
    quote = price_cart(
        [Line("ITEM1", 1)],
        catalog,
        today=date(2026, 1, 1),
        shipping="standard"
    )
    assert quote.shipping == Decimal("0.00")
    assert quote.total == Decimal("60.50")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_above_50():
    """Standard shipping is free when goods after discounts exceed 50.00"""
    # Subtotal: 60.00, no discounts
    # Goods after discounts: 60.00 > 50.00
    # Shipping: 0.00
    # Tax: 21% of 60.00 = 12.60
    # Total: 60.00 + 0.00 + 12.60 = 72.60
    catalog = {"ITEM1": Product("ITEM1", "Item", Decimal("60.00"))}
    quote = price_cart(
        [Line("ITEM1", 1)],
        catalog,
        today=date(2026, 1, 1),
        shipping="standard"
    )
    assert quote.shipping == Decimal("0.00")
    assert quote.total == Decimal("72.60")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_with_coupon_reaching_50():
    """Standard shipping is free when goods after coupon discount reach 50.00"""
    # Subtotal: 60.00, coupon -10.00
    # Goods after discount: 60.00 - 10.00 = 50.00
    # Shipping: 0.00
    # Tax: 21% of 50.00 = 10.50
    # Total: 60.00 - 10.00 + 0.00 + 10.50 = 60.50
    catalog = {"ITEM1": Product("ITEM1", "Item", Decimal("60.00"))}
    coupon = Coupon("SAVE10", "fixed", Decimal("10.00"))
    quote = price_cart(
        [Line("ITEM1", 1)],
        catalog,
        today=date(2026, 1, 1),
        coupon=coupon,
        shipping="standard"
    )
    assert quote.shipping == Decimal("0.00")
    assert quote.total == Decimal("60.50")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_charged_when_after_coupon_below_50():
    """Standard shipping charged when goods after coupon discount fall below 50.00"""
    # Subtotal: 60.00, coupon -11.00
    # Goods after discount: 60.00 - 11.00 = 49.00 < 50.00
    # Shipping: 4.99
    # Tax: 21% of (49.00 + 4.99) = 11.3379 → 11.34
    # Total: 60.00 - 11.00 + 4.99 + 11.34 = 65.33
    catalog = {"ITEM1": Product("ITEM1", "Item", Decimal("60.00"))}
    coupon = Coupon("SAVE11", "fixed", Decimal("11.00"))
    quote = price_cart(
        [Line("ITEM1", 1)],
        catalog,
        today=date(2026, 1, 1),
        coupon=coupon,
        shipping="standard"
    )
    assert quote.shipping == Decimal("4.99")
    assert quote.total == Decimal("65.33")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_with_loyalty_discount_reaching_50():
    """Standard shipping is free when goods after loyalty discount reach 50.00"""
    # Subtotal: 60.00, gold loyalty -5% = -3.00
    # Goods after discount: 60.00 - 3.00 = 57.00 >= 50.00
    # Shipping: 0.00
    # Tax: 21% of 57.00 = 11.97
    # Total: 60.00 - 3.00 + 0.00 + 11.97 = 68.97
    catalog = {"ITEM1": Product("ITEM1", "Item", Decimal("60.00"))}
    customer = Customer(tier="gold")
    quote = price_cart(
        [Line("ITEM1", 1)],
        catalog,
        today=date(2026, 1, 1),
        customer=customer,
        shipping="standard"
    )
    assert quote.shipping == Decimal("0.00")
    assert quote.total == Decimal("68.97")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_with_volume_discount_reaching_50():
    """Standard shipping is free when goods with volume discount reach 50.00"""
    # 15 units × 4.00 = 60.00, volume discount 10% = -6.00
    # Subtotal after volume discount: 54.00
    # Goods after all discounts: 54.00 >= 50.00
    # Shipping: 0.00
    # Tax: 21% of 54.00 = 11.34
    # Total: 54.00 + 0.00 + 11.34 = 65.34
    catalog = {"ITEM1": Product("ITEM1", "Item", Decimal("4.00"))}
    quote = price_cart(
        [Line("ITEM1", 15)],
        catalog,
        today=date(2026, 1, 1),
        shipping="standard"
    )
    assert quote.shipping == Decimal("0.00")
    assert quote.total == Decimal("65.34")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_empty_cart_no_charge():
    """Empty cart has no shipping charge per S1-AC5"""
    # Empty cart, all amounts are 0.00
    # Shipping: 0.00
    # Total: 0.00
    quote = price_cart(
        [],
        {},
        today=date(2026, 1, 1),
        shipping="standard"
    )
    assert quote.shipping == Decimal("0.00")
    assert quote.subtotal == Decimal("0.00")
    assert quote.discount == Decimal("0.00")
    assert quote.tax == Decimal("0.00")
    assert quote.total == Decimal("0.00")


# S5-AC2: Express shipping costs 9.99 and is never free

@pytest.mark.ac("S5-AC2")
def test_express_shipping_costs_9_99_small_order():
    """Express shipping costs 9.99 on small order"""
    # Subtotal: 30.00, no discounts
    # Goods: 30.00 < 50.00 (would normally qualify for free standard shipping, but not express)
    # Shipping: 9.99
    # Tax: 21% of (30.00 + 9.99) = 8.3979 → 8.40
    # Total: 30.00 + 9.99 + 8.40 = 48.39
    catalog = {"ITEM1": Product("ITEM1", "Item", Decimal("30.00"))}
    quote = price_cart(
        [Line("ITEM1", 1)],
        catalog,
        today=date(2026, 1, 1),
        shipping="express"
    )
    assert quote.shipping == Decimal("9.99")
    assert quote.total == Decimal("48.39")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_never_free_on_large_order():
    """Express shipping is never free, even when goods exceed 50.00"""
    # Subtotal: 100.00, no discounts
    # Goods: 100.00 >= 50.00 (would get free standard shipping)
    # Shipping: 9.99 (express never free)
    # Tax: 21% of (100.00 + 9.99) = 23.0979 → 23.10
    # Total: 100.00 + 9.99 + 23.10 = 133.09
    catalog = {"ITEM1": Product("ITEM1", "Item", Decimal("100.00"))}
    quote = price_cart(
        [Line("ITEM1", 1)],
        catalog,
        today=date(2026, 1, 1),
        shipping="express"
    )
    assert quote.shipping == Decimal("9.99")
    assert quote.total == Decimal("133.09")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_never_free_with_discounts():
    """Express shipping never becomes free, even with loyalty discount"""
    # Subtotal: 60.00, gold loyalty -5% = -3.00
    # Goods after discount: 57.00 >= 50.00 (would get free standard shipping)
    # Shipping: 9.99 (express never free)
    # Tax: 21% of (57.00 + 9.99) = 14.0679 → 14.07
    # Total: 60.00 - 3.00 + 9.99 + 14.07 = 81.06
    catalog = {"ITEM1": Product("ITEM1", "Item", Decimal("60.00"))}
    customer = Customer(tier="gold")
    quote = price_cart(
        [Line("ITEM1", 1)],
        catalog,
        today=date(2026, 1, 1),
        customer=customer,
        shipping="express"
    )
    assert quote.shipping == Decimal("9.99")
    assert quote.total == Decimal("81.06")


# S5-AC3: Invalid shipping method raises CartError

@pytest.mark.ac("S5-AC3")
def test_invalid_shipping_method_ground_raises_error():
    """Invalid shipping method 'ground' raises CartError"""
    catalog = {"ITEM1": Product("ITEM1", "Item", Decimal("50.00"))}
    with pytest.raises(CartError):
        price_cart(
            [Line("ITEM1", 1)],
            catalog,
            today=date(2026, 1, 1),
            shipping="ground"
        )


@pytest.mark.ac("S5-AC3")
def test_invalid_shipping_method_overnight_raises_error():
    """Invalid shipping method 'overnight' raises CartError"""
    catalog = {"ITEM1": Product("ITEM1", "Item", Decimal("50.00"))}
    with pytest.raises(CartError):
        price_cart(
            [Line("ITEM1", 1)],
            catalog,
            today=date(2026, 1, 1),
            shipping="overnight"
        )


@pytest.mark.ac("S5-AC3")
def test_invalid_shipping_method_empty_string_raises_error():
    """Empty string as shipping method raises CartError"""
    catalog = {"ITEM1": Product("ITEM1", "Item", Decimal("50.00"))}
    with pytest.raises(CartError):
        price_cart(
            [Line("ITEM1", 1)],
            catalog,
            today=date(2026, 1, 1),
            shipping=""
        )


@pytest.mark.ac("S5-AC3")
def test_invalid_shipping_method_typo_raises_error():
    """Typo in shipping method ('standart' instead of 'standard') raises CartError"""
    catalog = {"ITEM1": Product("ITEM1", "Item", Decimal("50.00"))}
    with pytest.raises(CartError):
        price_cart(
            [Line("ITEM1", 1)],
            catalog,
            today=date(2026, 1, 1),
            shipping="standart"
        )
```