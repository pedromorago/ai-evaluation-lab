import pytest
from datetime import date
from decimal import Decimal
from checkout import price_cart, Product, Line, Customer, Coupon

TODAY = date(2024, 1, 1)


# S6-AC1: VAT is 21% of the goods after discounts plus shipping
@pytest.mark.ac("S6-AC1")
def test_tax_basic_no_discount():
    """Tax is 21% of (subtotal - discount + shipping)"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("100.00"))}
    lines = [Line("ITEM", 1)]
    quote = price_cart(lines, catalog, today=TODAY)
    
    # Subtotal: 100.00, discount: 0.00, shipping: 4.99
    # Tax base: 100.00 + 4.99 = 104.99
    # Tax: 104.99 * 0.21 = 22.0479 -> 22.05
    assert quote.tax == Decimal("22.05")


@pytest.mark.ac("S6-AC1")
def test_tax_with_volume_discount():
    """Tax base accounts for volume discount"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("10.00"))}
    lines = [Line("ITEM", 10)]  # 10% volume discount
    quote = price_cart(lines, catalog, today=TODAY)
    
    # Subtotal: 100.00, volume discount: 10.00, shipping: 4.99
    # Tax base: 100.00 - 10.00 + 4.99 = 94.99
    # Tax: 94.99 * 0.21 = 19.9479 -> 19.95
    assert quote.tax == Decimal("19.95")


@pytest.mark.ac("S6-AC1")
def test_tax_with_loyalty_discount():
    """Tax base accounts for loyalty discount"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("100.00"))}
    lines = [Line("ITEM", 1)]
    customer = Customer(tier="gold")
    quote = price_cart(lines, catalog, today=TODAY, customer=customer)
    
    # Subtotal: 100.00, loyalty: 5.00, shipping: 4.99
    # Tax base: 100.00 - 5.00 + 4.99 = 99.99
    # Tax: 99.99 * 0.21 = 20.9979 -> 21.00
    assert quote.tax == Decimal("21.00")


@pytest.mark.ac("S6-AC1")
def test_tax_with_percent_coupon():
    """Tax base accounts for percent coupon discount"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("100.00"))}
    lines = [Line("ITEM", 1)]
    coupon = Coupon("SAVE10", "percent", Decimal("10"))
    quote = price_cart(lines, catalog, today=TODAY, coupon=coupon)
    
    # Subtotal: 100.00, coupon: 10.00, shipping: 4.99
    # Tax base: 100.00 - 10.00 + 4.99 = 94.99
    # Tax: 94.99 * 0.21 = 19.9479 -> 19.95
    assert quote.tax == Decimal("19.95")


@pytest.mark.ac("S6-AC1")
def test_tax_with_fixed_coupon():
    """Tax base accounts for fixed coupon discount"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("100.00"))}
    lines = [Line("ITEM", 1)]
    coupon = Coupon("FIXED5", "fixed", Decimal("5.00"))
    quote = price_cart(lines, catalog, today=TODAY, coupon=coupon)
    
    # Subtotal: 100.00, fixed: 5.00, shipping: 4.99
    # Tax base: 100.00 - 5.00 + 4.99 = 94.99
    # Tax: 94.99 * 0.21 = 19.9479 -> 19.95
    assert quote.tax == Decimal("19.95")


@pytest.mark.ac("S6-AC1")
def test_tax_with_express_shipping():
    """Tax base includes express shipping cost"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("100.00"))}
    lines = [Line("ITEM", 1)]
    quote = price_cart(lines, catalog, today=TODAY, shipping="express")
    
    # Subtotal: 100.00, shipping: 9.99
    # Tax base: 100.00 + 9.99 = 109.99
    # Tax: 109.99 * 0.21 = 23.0979 -> 23.10
    assert quote.tax == Decimal("23.10")


@pytest.mark.ac("S6-AC1")
def test_tax_with_free_shipping():
    """Tax base includes free shipping (0.00)"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("100.00"))}
    lines = [Line("ITEM", 6)]  # 600.00, triggers free shipping
    quote = price_cart(lines, catalog, today=TODAY)
    
    # Subtotal: 600.00, shipping: 0.00
    # Tax base: 600.00 + 0.00 = 600.00
    # Tax: 600.00 * 0.21 = 126.00
    assert quote.tax == Decimal("126.00")


@pytest.mark.ac("S6-AC2")
def test_rounding_half_up_subtotal():
    """Subtotal rounded half-up to cent"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("1.005"))}
    lines = [Line("ITEM", 1)]
    quote = price_cart(lines, catalog, today=TODAY)
    
    # 1.005 rounds half-up to 1.01
    assert quote.subtotal == Decimal("1.01")


@pytest.mark.ac("S6-AC2")
def test_rounding_half_up_discount():
    """Each discount rounded half-up to cent"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("100") / Decimal("3"))}
    lines = [Line("ITEM", 1)]
    coupon = Coupon("TEST", "percent", Decimal("10"))
    quote = price_cart(lines, catalog, today=TODAY, coupon=coupon)
    
    # Subtotal: 33.333... -> 33.33
    # Discount: 33.33 * 0.10 = 3.333 -> 3.33
    assert quote.subtotal == Decimal("33.33")
    assert quote.discount == Decimal("3.33")


@pytest.mark.ac("S6-AC2")
def test_rounding_half_up_tax():
    """Tax rounded half-up to cent"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("10") / Decimal("3"))}
    lines = [Line("ITEM", 1)]
    quote = price_cart(lines, catalog, today=TODAY)
    
    # Subtotal: 3.333... -> 3.33
    # Tax base: 3.33 + 4.99 = 8.32
    # Tax: 8.32 * 0.21 = 1.7472 -> 1.75
    assert quote.tax == Decimal("1.75")


@pytest.mark.ac("S6-AC2")
def test_total_formula():
    """Total equals subtotal - discount + shipping + tax exactly"""
    catalog = {
        "A": Product("A", "Item A", Decimal("33.33")),
        "B": Product("B", "Item B", Decimal("66.67"))
    }
    lines = [Line("A", 1), Line("B", 1)]
    customer = Customer(tier="gold")
    quote = price_cart(lines, catalog, today=TODAY, customer=customer)
    
    expected_total = quote.subtotal - quote.discount + quote.shipping + quote.tax
    assert quote.total == expected_total


@pytest.mark.ac("S6-AC2")
def test_rounding_subtotal_before_discount():
    """Subtotal rounded before calculating discount"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("10.001"))}
    lines = [Line("ITEM", 1)]
    coupon = Coupon("TEST", "percent", Decimal("10"))
    quote = price_cart(lines, catalog, today=TODAY, coupon=coupon)
    
    # Subtotal: 10.001 -> 10.00
    # Discount: 10.00 * 0.10 = 1.00
    assert quote.subtotal == Decimal("10.00")
    assert quote.discount == Decimal("1.00")


@pytest.mark.ac("S6-AC2")
def test_complex_rounding_integration():
    """All rounding rules applied in sequence"""
    catalog = {
        "A": Product("A", "Item A", Decimal("33.33")),
        "B": Product("B", "Item B", Decimal("66.67"))
    }
    lines = [Line("A", 1), Line("B", 1)]
    customer = Customer(tier="gold")
    quote = price_cart(lines, catalog, today=TODAY, customer=customer)
    
    # Subtotal: 33.33 + 66.67 = 100.00
    # Loyalty: 100.00 * 0.05 = 5.00
    # Shipping: 4.99
    # Tax base: 100.00 - 5.00 + 4.99 = 99.99
    # Tax: 99.99 * 0.21 = 20.9979 -> 21.00
    # Total: 100.00 - 5.00 + 4.99 + 21.00 = 120.99
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("5.00")
    assert quote.tax == Decimal("21.00")
    assert quote.total == Decimal("120.99")


@pytest.mark.ac("S6-AC3")
def test_applied_volume_discount_single_sku():
    """applied lists volume:<SKU> for each volume-discounted product"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("10.00"))}
    lines = [Line("ITEM", 10)]
    quote = price_cart(lines, catalog, today=TODAY)
    
    assert "volume:ITEM" in quote.applied


@pytest.mark.ac("S6-AC3")
def test_applied_volume_discount_order():
    """Volume discounts listed in order of first appearance"""
    catalog = {
        "A": Product("A", "Item A", Decimal("10.00")),
        "B": Product("B", "Item B", Decimal("10.00")),
        "C": Product("C", "Item C", Decimal("10.00"))
    }
    lines = [Line("A", 10), Line("B", 5), Line("C", 10)]
    quote = price_cart(lines, catalog, today=TODAY)
    
    assert quote.applied == ("volume:A", "volume:C")


@pytest.mark.ac("S6-AC3")
def test_applied_loyalty():
    """applied lists loyalty when gold tier customer"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("100.00"))}
    lines = [Line("ITEM", 1)]
    customer = Customer(tier="gold")
    quote = price_cart(lines, catalog, today=TODAY, customer=customer)
    
    assert "loyalty" in quote.applied


@pytest.mark.ac("S6-AC3")
def test_applied_percent_coupon():
    """applied lists coupon:<CODE> for percent coupon"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("100.00"))}
    lines = [Line("ITEM", 1)]
    coupon = Coupon("SAVE10", "percent", Decimal("10"))
    quote = price_cart(lines, catalog, today=TODAY, coupon=coupon)
    
    assert "coupon:SAVE10" in quote.applied


@pytest.mark.ac("S6-AC3")
def test_applied_fixed_coupon():
    """applied lists coupon:<CODE> for fixed coupon"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("100.00"))}
    lines = [Line("ITEM", 1)]
    coupon = Coupon("FIXED5", "fixed", Decimal("5.00"))
    quote = price_cart(lines, catalog, today=TODAY, coupon=coupon)
    
    assert "coupon:FIXED5" in quote.applied


@pytest.mark.ac("S6-AC3")
def test_applied_loyalty_vs_percent_coupon_coupon_wins():
    """When percent coupon larger, coupon in applied (not loyalty)"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("100.00"))}
    lines = [Line("ITEM", 1)]
    customer = Customer(tier="gold")
    coupon = Coupon("SAVE10", "percent", Decimal("10"))
    quote = price_cart(lines, catalog, today=TODAY, customer=customer, coupon=coupon)
    
    assert "coupon:SAVE10" in quote.applied
    assert "loyalty" not in quote.applied


@pytest.mark.ac("S6-AC3")
def test_applied_loyalty_vs_percent_coupon_loyalty_wins():
    """When loyalty larger, loyalty in applied (not coupon)"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("100.00"))}
    lines = [Line("ITEM", 1)]
    customer = Customer(tier="gold")
    coupon = Coupon("SAVE3", "percent", Decimal("3"))
    quote = price_cart(lines, catalog, today=TODAY, customer=customer, coupon=coupon)
    
    assert "loyalty" in quote.applied
    assert "coupon:SAVE3" not in quote.applied


@pytest.mark.ac("S6-AC3")
def test_applied_loyalty_vs_percent_coupon_equal_coupon_wins():
    """When equal percentage, coupon wins per S4-AC2"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("100.00"))}
    lines = [Line("ITEM", 1)]
    customer = Customer(tier="gold")
    coupon = Coupon("SAVE5", "percent", Decimal("5"))
    quote = price_cart(lines, catalog, today=TODAY, customer=customer, coupon=coupon)
    
    assert "coupon:SAVE5" in quote.applied
    assert "loyalty" not in quote.applied


@pytest.mark.ac("S6-AC3")
def test_applied_order_volume_loyalty_fixed_coupon():
    """applied order: volume, then loyalty, then fixed coupon"""
    catalog = {
        "A": Product("A", "Item A", Decimal("10.00")),
        "B": Product("B", "Item B", Decimal("10.00"))
    }
    lines = [Line("A", 10), Line("B", 1)]
    customer = Customer(tier="gold")
    coupon = Coupon("FIXED5", "fixed", Decimal("5.00"))
    quote = price_cart(lines, catalog, today=TODAY, customer=customer, coupon=coupon)
    
    assert quote.applied == ("volume:A", "loyalty", "coupon:FIXED5")


@pytest.mark.ac("S6-AC3")
def test_applied_order_volume_then_percent_coupon():
    """applied order: volume discounts, then percent coupon"""
    catalog = {
        "A": Product("A", "Item A", Decimal("10.00")),
        "B": Product("B", "Item B", Decimal("10.00"))
    }
    lines = [Line("A", 10), Line("B", 1)]
    coupon = Coupon("SAVE10", "percent", Decimal("10"))
    quote = price_cart(lines, catalog, today=TODAY, coupon=coupon)
    
    assert quote.applied == ("volume:A", "coupon:SAVE10")


@pytest.mark.ac("S6-AC3")
def test_applied_empty_when_no_discounts():
    """applied is empty tuple when nothing is discounted"""
    catalog = {"ITEM": Product("ITEM", "Test", Decimal("10.00"))}
    lines = [Line("ITEM", 1)]
    quote = price_cart(lines, catalog, today=TODAY)
    
    assert quote.applied == ()


@pytest.mark.ac("S6-AC3")
def test_applied_empty_cart():
    """applied is empty for empty cart"""
    quote = price_cart([], {}, today=TODAY)
    assert quote.applied == ()


@pytest.mark.ac("S6-AC3")
def test_applied_multiple_volume_discounts_order():
    """Multiple volume discounts in order of first appearance"""
    catalog = {
        "SKU1": Product("SKU1", "Item 1", Decimal("10.00")),
        "SKU2": Product("SKU2", "Item 2", Decimal("10.00")),
        "SKU3": Product("SKU3", "Item 3", Decimal("10.00")),
        "SKU4": Product("SKU4", "Item 4", Decimal("10.00"))
    }
    lines = [Line("SKU1", 10), Line("SKU2", 5), Line("SKU3", 15), Line("SKU4", 10)]
    quote = price_cart(lines, catalog, today=TODAY)
    
    assert quote.applied == ("volume:SKU1", "volume:SKU3", "volume:SKU4")
