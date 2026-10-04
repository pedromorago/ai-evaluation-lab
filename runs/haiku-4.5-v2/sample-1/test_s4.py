import pytest
from decimal import Decimal
from datetime import date
from checkout import (
    Product,
    Line,
    Customer,
    Coupon,
    price_cart,
)


# S4-AC1: Gold tier gets 5% loyalty discount, standard tier gets none

@pytest.mark.ac("S4-AC1")
def test_gold_customer_receives_5_percent_loyalty_discount():
    """Gold tier should get exactly 5% loyalty discount on subtotal"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    customer = Customer(tier="gold")
    today = date(2026, 10, 3)
    
    # Subtotal: 100.00 * 1 = 100.00
    # Loyalty discount: 100.00 * 0.05 = 5.00
    
    quote = price_cart(lines, catalog, today=today, customer=customer)
    
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("5.00")
    assert "loyalty" in quote.applied


@pytest.mark.ac("S4-AC1")
def test_standard_customer_receives_no_loyalty_discount():
    """Standard tier should receive no loyalty discount"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    customer = Customer(tier="standard")
    today = date(2026, 10, 3)
    
    # Subtotal: 100.00
    # No loyalty for standard tier
    # Discount: 0.00
    
    quote = price_cart(lines, catalog, today=today, customer=customer)
    
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("0.00")
    assert "loyalty" not in quote.applied


@pytest.mark.ac("S4-AC1")
def test_default_customer_is_standard_tier_no_loyalty():
    """Customer() with no tier argument defaults to standard (no loyalty)"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    today = date(2026, 10, 3)
    
    # Default customer is standard tier
    # Subtotal: 100.00
    # No loyalty discount
    
    quote = price_cart(lines, catalog, today=today)
    
    assert quote.discount == Decimal("0.00")
    assert "loyalty" not in quote.applied


@pytest.mark.ac("S4-AC1")
def test_loyalty_applied_to_subtotal_after_volume_discounts():
    """Loyalty discount should be based on subtotal after volume discounts"""
    catalog = {
        "BULK": Product(sku="BULK", name="Bulk Item", unit_price=Decimal("10.00"))
    }
    lines = [Line(sku="BULK", quantity=10)]
    customer = Customer(tier="gold")
    today = date(2026, 10, 3)
    
    # Line total: 10.00 * 10 = 100.00
    # Volume discount (10+ units): 100.00 * 0.10 = 10.00
    # Subtotal: 90.00
    # Loyalty on subtotal: 90.00 * 0.05 = 4.50
    # Total discount: 10.00 + 4.50 = 14.50
    
    quote = price_cart(lines, catalog, today=today, customer=customer)
    
    assert quote.subtotal == Decimal("90.00")
    assert quote.discount == Decimal("14.50")
    assert "volume:BULK" in quote.applied
    assert "loyalty" in quote.applied


@pytest.mark.ac("S4-AC1")
def test_loyalty_with_multiple_items_applied_to_combined_subtotal():
    """Loyalty should be based on combined subtotal of all items"""
    catalog = {
        "ITEM1": Product(sku="ITEM1", name="Item 1", unit_price=Decimal("50.00")),
        "ITEM2": Product(sku="ITEM2", name="Item 2", unit_price=Decimal("30.00")),
    }
    lines = [
        Line(sku="ITEM1", quantity=1),
        Line(sku="ITEM2", quantity=1),
    ]
    customer = Customer(tier="gold")
    today = date(2026, 10, 3)
    
    # Subtotal: 50.00 + 30.00 = 80.00
    # Loyalty: 80.00 * 0.05 = 4.00
    
    quote = price_cart(lines, catalog, today=today, customer=customer)
    
    assert quote.subtotal == Decimal("80.00")
    assert quote.discount == Decimal("4.00")
    assert "loyalty" in quote.applied


@pytest.mark.ac("S4-AC1")
def test_loyalty_discount_rounded_half_up():
    """Loyalty discount should be rounded half up to the cent"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.10"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    customer = Customer(tier="gold")
    today = date(2026, 10, 3)
    
    # Subtotal: 100.10
    # Loyalty: 100.10 * 0.05 = 5.005 -> rounds to 5.01 (half up)
    
    quote = price_cart(lines, catalog, today=today, customer=customer)
    
    assert quote.subtotal == Decimal("100.10")
    assert quote.discount == Decimal("5.01")


@pytest.mark.ac("S4-AC1")
def test_empty_cart_no_loyalty_discount():
    """Empty cart should have no loyalty discount despite gold tier"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = []
    customer = Customer(tier="gold")
    today = date(2026, 10, 3)
    
    # Empty cart: subtotal 0, no discounts, no applied items
    
    quote = price_cart(lines, catalog, today=today, customer=customer)
    
    assert quote.subtotal == Decimal("0.00")
    assert quote.discount == Decimal("0.00")
    assert quote.applied == ()


# S4-AC2: Loyalty and percent coupon don't stack (max wins, coupon if equal)

@pytest.mark.ac("S4-AC2")
def test_loyalty_larger_than_percent_coupon_loyalty_applies():
    """When loyalty > percent coupon, only loyalty applies"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="SMALL", kind="percent", value=Decimal("3"))
    today = date(2026, 10, 3)
    
    # Subtotal: 100.00
    # Loyalty: 100.00 * 0.05 = 5.00
    # Coupon: 100.00 * 0.03 = 3.00
    # Loyalty is larger, so only loyalty applies
    # Discount: 5.00
    
    quote = price_cart(lines, catalog, today=today, customer=customer, coupon=coupon)
    
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("5.00")
    assert quote.applied == ("loyalty",)


@pytest.mark.ac("S4-AC2")
def test_percent_coupon_larger_than_loyalty_coupon_applies():
    """When percent coupon > loyalty, only coupon applies"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="LARGE", kind="percent", value=Decimal("8"))
    today = date(2026, 10, 3)
    
    # Subtotal: 100.00
    # Loyalty: 100.00 * 0.05 = 5.00
    # Coupon: 100.00 * 0.08 = 8.00
    # Coupon is larger, so only coupon applies
    # Discount: 8.00
    
    quote = price_cart(lines, catalog, today=today, customer=customer, coupon=coupon)
    
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("8.00")
    assert quote.applied == ("coupon:LARGE",)


@pytest.mark.ac("S4-AC2")
def test_loyalty_and_percent_coupon_equal_coupon_wins():
    """When loyalty equals percent coupon, coupon wins"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="EQUAL", kind="percent", value=Decimal("5"))
    today = date(2026, 10, 3)
    
    # Subtotal: 100.00
    # Loyalty: 100.00 * 0.05 = 5.00
    # Coupon: 100.00 * 0.05 = 5.00
    # Equal, but coupon wins per spec
    # Discount: 5.00
    
    quote = price_cart(lines, catalog, today=today, customer=customer, coupon=coupon)
    
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("5.00")
    assert quote.applied == ("coupon:EQUAL",)


@pytest.mark.ac("S4-AC2")
def test_loyalty_and_fixed_coupon_both_apply():
    """Fixed coupon stacks with loyalty, both apply"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="FIXED-10", kind="fixed", value=Decimal("10.00"))
    today = date(2026, 10, 3)
    
    # Subtotal: 100.00
    # Loyalty: 100.00 * 0.05 = 5.00
    # Remaining after loyalty: 95.00
    # Fixed coupon: 10.00 (off the remaining 95.00)
    # Total discount: 5.00 + 10.00 = 15.00
    
    quote = price_cart(lines, catalog, today=today, customer=customer, coupon=coupon)
    
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("15.00")
    assert quote.applied == ("loyalty", "coupon:FIXED-10")


@pytest.mark.ac("S4-AC2")
def test_fixed_coupon_taken_off_after_loyalty():
    """Fixed coupon should be deducted after loyalty discount is applied"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("50.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="FIXED-15", kind="fixed", value=Decimal("15.00"))
    today = date(2026, 10, 3)
    
    # Subtotal: 50.00
    # Loyalty: 50.00 * 0.05 = 2.50
    # Amount after loyalty: 50.00 - 2.50 = 47.50
    # Fixed coupon: 15.00 (deducted from 47.50)
    # Total discount: 2.50 + 15.00 = 17.50
    
    quote = price_cart(lines, catalog, today=today, customer=customer, coupon=coupon)
    
    assert quote.subtotal == Decimal("50.00")
    assert quote.discount == Decimal("17.50")
    assert quote.applied == ("loyalty", "coupon:FIXED-15")


@pytest.mark.ac("S4-AC2")
def test_fixed_coupon_capped_at_remaining_after_loyalty():
    """Fixed coupon should not reduce goods below 0 (per S3-AC2)"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("10.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="HUGE", kind="fixed", value=Decimal("50.00"))
    today = date(2026, 10, 3)
    
    # Subtotal: 10.00
    # Loyalty: 10.00 * 0.05 = 0.50
    # Remaining: 9.50
    # Fixed coupon requested: 50.00, but max is 9.50
    # Total discount: 0.50 + 9.50 = 10.00
    
    quote = price_cart(lines, catalog, today=today, customer=customer, coupon=coupon)
    
    assert quote.subtotal == Decimal("10.00")
    assert quote.discount == Decimal("10.00")
    assert quote.applied == ("loyalty", "coupon:HUGE")


# Combined: loyalty with volume discounts and percent coupon

@pytest.mark.ac("S4-AC1", "S4-AC2")
def test_loyalty_after_volume_vs_percent_coupon_loyalty_larger():
    """Loyalty (after volume) vs percent coupon, loyalty is larger"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("10.00"))
    }
    lines = [Line(sku="ITEM", quantity=10)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="TINY", kind="percent", value=Decimal("2"))
    today = date(2026, 10, 3)
    
    # Line total: 100.00, volume discount 10%: 10.00
    # Subtotal: 90.00
    # Loyalty: 90.00 * 0.05 = 4.50
    # Coupon: 90.00 * 0.02 = 1.80
    # Loyalty larger, applies
    # Total discount: 10.00 + 4.50 = 14.50
    
    quote = price_cart(lines, catalog, today=today, customer=customer, coupon=coupon)
    
    assert quote.subtotal == Decimal("90.00")
    assert quote.discount == Decimal("14.50")
    assert quote.applied == ("volume:ITEM", "loyalty")


@pytest.mark.ac("S4-AC1", "S4-AC2")
def test_loyalty_after_volume_vs_percent_coupon_coupon_larger():
    """Loyalty (after volume) vs percent coupon, coupon is larger"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("10.00"))
    }
    lines = [Line(sku="ITEM", quantity=10)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="GOOD", kind="percent", value=Decimal("10"))
    today = date(2026, 10, 3)
    
    # Subtotal after volume: 90.00
    # Loyalty: 90.00 * 0.05 = 4.50
    # Coupon: 90.00 * 0.10 = 9.00
    # Coupon larger, applies
    # Total discount: 10.00 + 9.00 = 19.00
    
    quote = price_cart(lines, catalog, today=today, customer=customer, coupon=coupon)
    
    assert quote.subtotal == Decimal("90.00")
    assert quote.discount == Decimal("19.00")
    assert quote.applied == ("volume:ITEM", "coupon:GOOD")


@pytest.mark.ac("S4-AC1", "S4-AC2")
def test_loyalty_after_volume_with_fixed_coupon():
    """Loyalty (after volume) and fixed coupon both apply"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("10.00"))
    }
    lines = [Line(sku="ITEM", quantity=10)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="FIXED-5", kind="fixed", value=Decimal("5.00"))
    today = date(2026, 10, 3)
    
    # Subtotal after volume: 90.00
    # Loyalty: 90.00 * 0.05 = 4.50
    # Remaining: 85.50
    # Fixed coupon: 5.00
    # Total discount: 10.00 + 4.50 + 5.00 = 19.50
    
    quote = price_cart(lines, catalog, today=today, customer=customer, coupon=coupon)
    
    assert quote.subtotal == Decimal("90.00")
    assert quote.discount == Decimal("19.50")
    assert quote.applied == ("volume:ITEM", "loyalty", "coupon:FIXED-5")


@pytest.mark.ac("S4-AC2")
def test_standard_customer_percent_coupon_no_loyalty():
    """Standard customer with percent coupon gets only coupon (no loyalty)"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    customer = Customer(tier="standard")
    coupon = Coupon(code="PROMO", kind="percent", value=Decimal("10"))
    today = date(2026, 10, 3)
    
    # Subtotal: 100.00
    # No loyalty (standard tier)
    # Coupon: 100.00 * 0.10 = 10.00
    # Discount: 10.00
    
    quote = price_cart(lines, catalog, today=today, customer=customer, coupon=coupon)
    
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("10.00")
    assert quote.applied == ("coupon:PROMO",)


@pytest.mark.ac("S4-AC2")
def test_standard_customer_fixed_coupon_no_loyalty():
    """Standard customer with fixed coupon gets only coupon (no loyalty)"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("50.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    customer = Customer(tier="standard")
    coupon = Coupon(code="FIXED-5", kind="fixed", value=Decimal("5.00"))
    today = date(2026, 10, 3)
    
    # Subtotal: 50.00
    # No loyalty (standard tier)
    # Fixed coupon: 5.00
    # Discount: 5.00
    
    quote = price_cart(lines, catalog, today=today, customer=customer, coupon=coupon)
    
    assert quote.subtotal == Decimal("50.00")
    assert quote.discount == Decimal("5.00")
    assert quote.applied == ("coupon:FIXED-5",)
