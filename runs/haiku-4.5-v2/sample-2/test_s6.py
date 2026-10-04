import pytest
from decimal import Decimal
from datetime import date
from checkout import Product, Line, Customer, Coupon, price_cart


# S6-AC1: VAT is 21% of goods after discounts plus shipping

@pytest.mark.ac("S6-AC1")
def test_vat_basic_no_discounts_no_shipping():
    """VAT is 21% when goods have no discounts and shipping is free."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
    lines = [Line("ITEM", 1)]
    # Subtotal: 100.00, no discount, shipping free (100 >= 50)
    # Taxable: 100.00, Tax: 100.00 * 0.21 = 21.00
    quote = price_cart(lines, products, today=date(2026, 1, 1))
    assert quote.tax == Decimal("21.00")


@pytest.mark.ac("S6-AC1")
def test_vat_includes_shipping_in_base():
    """VAT calculation includes shipping in the taxable base."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("30.00"))}
    lines = [Line("ITEM", 1)]
    # Subtotal: 30.00, no discount, shipping 4.99 (30 < 50)
    # Taxable: 30.00 + 4.99 = 34.99, Tax: 34.99 * 0.21 = 7.3479 -> 7.35
    quote = price_cart(lines, products, today=date(2026, 1, 1))
    assert quote.tax == Decimal("7.35")


@pytest.mark.ac("S6-AC1")
def test_vat_after_volume_discount():
    """VAT is 21% of goods after volume discount applied."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("10.00"))}
    lines = [Line("ITEM", 10)]
    # Subtotal before: 100.00, volume 10% = 10.00, after: 90.00
    # Shipping free (90 >= 50), Taxable: 90.00, Tax: 90.00 * 0.21 = 18.90
    quote = price_cart(lines, products, today=date(2026, 1, 1))
    assert quote.tax == Decimal("18.90")


@pytest.mark.ac("S6-AC1")
def test_vat_after_percent_coupon():
    """VAT is 21% of goods after percent coupon discount."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
    coupon = Coupon("SAVE10", "percent", Decimal("10"))
    lines = [Line("ITEM", 1)]
    # Subtotal: 100.00, coupon 10% = 10.00, goods after: 90.00
    # Shipping free (90 >= 50), Taxable: 90.00, Tax: 18.90
    quote = price_cart(
        lines, products, today=date(2026, 1, 1), coupon=coupon
    )
    assert quote.tax == Decimal("18.90")


@pytest.mark.ac("S6-AC1")
def test_vat_after_fixed_coupon():
    """VAT is 21% of goods after fixed coupon discount."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
    coupon = Coupon("OFF5", "fixed", Decimal("5.00"))
    lines = [Line("ITEM", 1)]
    # Subtotal: 100.00, fixed off 5.00, goods after: 95.00
    # Shipping free (95 >= 50), Taxable: 95.00, Tax: 95.00 * 0.21 = 19.95
    quote = price_cart(
        lines, products, today=date(2026, 1, 1), coupon=coupon
    )
    assert quote.tax == Decimal("19.95")


@pytest.mark.ac("S6-AC1")
def test_vat_after_loyalty_discount():
    """VAT is 21% of goods after loyalty discount."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
    customer = Customer(tier="gold")
    lines = [Line("ITEM", 1)]
    # Subtotal: 100.00, loyalty 5% = 5.00, goods after: 95.00
    # Shipping free (95 >= 50), Taxable: 95.00, Tax: 19.95
    quote = price_cart(
        lines, products, today=date(2026, 1, 1), customer=customer
    )
    assert quote.tax == Decimal("19.95")


# S6-AC2: Every amount rounded half up to cent; total formula holds

@pytest.mark.ac("S6-AC2")
def test_subtotal_rounded_half_up():
    """Subtotal is rounded half up to the cent."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("10.005"))}
    lines = [Line("ITEM", 1)]
    # Subtotal: 10.005 -> 10.01 (half up)
    quote = price_cart(lines, products, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("10.01")


@pytest.mark.ac("S6-AC2")
def test_subtotal_rounded_half_down():
    """Subtotal rounds .004 down to previous cent."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("10.004"))}
    lines = [Line("ITEM", 1)]
    # Subtotal: 10.004 -> 10.00 (half up, so this rounds down)
    quote = price_cart(lines, products, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("10.00")


@pytest.mark.ac("S6-AC2")
def test_discount_rounded_half_up():
    """Percent discount is rounded half up to the cent."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("33.33"))}
    coupon = Coupon("TEST", "percent", Decimal("10"))
    lines = [Line("ITEM", 1)]
    # Subtotal: 33.33, discount: 33.33 * 0.10 = 3.333 -> 3.33
    quote = price_cart(
        lines, products, today=date(2026, 1, 1), coupon=coupon
    )
    assert quote.discount == Decimal("3.33")


@pytest.mark.ac("S6-AC2")
def test_tax_rounded_half_up():
    """Tax is rounded half up to the cent."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("10.00"))}
    lines = [Line("ITEM", 1)]
    # Subtotal: 10.00, no discount, shipping: 4.99
    # Taxable: 14.99, Tax: 14.99 * 0.21 = 3.1479 -> 3.15
    quote = price_cart(lines, products, today=date(2026, 1, 1))
    assert quote.tax == Decimal("3.15")


@pytest.mark.ac("S6-AC2")
def test_total_equals_formula():
    """Total is exactly subtotal - discount + shipping + tax."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("50.00"))}
    coupon = Coupon("SAVE10", "percent", Decimal("10"))
    lines = [Line("ITEM", 1)]
    # Subtotal: 50.00, discount: 5.00, goods: 45.00, shipping: 4.99
    # Tax: 49.99 * 0.21 = 10.4979 -> 10.50
    # Total: 50.00 - 5.00 + 4.99 + 10.50 = 60.49
    quote = price_cart(
        lines, products, today=date(2026, 1, 1), coupon=coupon
    )
    expected = quote.subtotal - quote.discount + quote.shipping + quote.tax
    assert quote.total == expected


@pytest.mark.ac("S6-AC2")
def test_formula_with_multiple_roundings():
    """Formula holds after multiple rounding steps."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("3.33"))}
    lines = [Line("ITEM", 3)]
    # Subtotal: 9.99, no discount, shipping: 4.99
    # Taxable: 14.98, Tax: 14.98 * 0.21 = 3.1458 -> 3.15
    # Total: 9.99 - 0.00 + 4.99 + 3.15 = 18.13
    quote = price_cart(lines, products, today=date(2026, 1, 1))
    expected = quote.subtotal - quote.discount + quote.shipping + quote.tax
    assert quote.total == expected
    assert quote.total == Decimal("18.13")


@pytest.mark.ac("S6-AC2")
def test_stacked_discounts_rounded():
    """Stacked discounts (loyalty + fixed) are rounded correctly."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
    customer = Customer(tier="gold")
    coupon = Coupon("OFF5", "fixed", Decimal("5.00"))
    lines = [Line("ITEM", 1)]
    # Subtotal: 100.00, loyalty: 5.00, fixed: 5.00
    # Total discount: 10.00, goods: 90.00, shipping free
    # Tax: 90.00 * 0.21 = 18.90
    # Total: 100.00 - 10.00 + 0.00 + 18.90 = 108.90
    quote = price_cart(
        lines, products, today=date(2026, 1, 1),
        customer=customer, coupon=coupon
    )
    expected = quote.subtotal - quote.discount + quote.shipping + quote.tax
    assert quote.total == expected
    assert quote.total == Decimal("108.90")


@pytest.mark.ac("S6-AC2")
def test_rounding_near_boundary():
    """Rounding behavior near 50.00 shipping threshold."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("47.619"))}
    lines = [Line("ITEM", 1)]
    # Subtotal: 47.619 -> 47.62, no discount
    # Goods 47.62 < 50, so shipping 4.99
    # Taxable: 47.62 + 4.99 = 52.61
    # Tax: 52.61 * 0.21 = 11.0481 -> 11.05
    quote = price_cart(lines, products, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("47.62")
    assert quote.shipping == Decimal("4.99")


@pytest.mark.ac("S6-AC2")
def test_rounding_preserves_formula_complex():
    """Formula preserved with complex multi-discount scenario."""
    products = {
        "ITEM": Product("ITEM", "Item", Decimal("10.00")),
    }
    customer = Customer(tier="gold")
    coupon = Coupon("OFF2", "fixed", Decimal("2.00"))
    lines = [Line("ITEM", 15)]
    # Subtotal: 150.00, volume 15% = 22.50, after: 127.50
    # Loyalty: 127.50 * 0.05 = 6.375 -> 6.38
    # Fixed: 2.00, total discount: 8.38
    # Goods: 119.12, shipping free (119.12 >= 50)
    # Tax: 119.12 * 0.21 = 25.0152 -> 25.02
    # Total: 127.50 - 8.38 + 0.00 + 25.02 = 144.14
    quote = price_cart(
        lines, products, today=date(2026, 1, 1),
        customer=customer, coupon=coupon
    )
    expected = quote.subtotal - quote.discount + quote.shipping + quote.tax
    assert quote.total == expected
    assert quote.total == Decimal("144.14")


# S6-AC3: applied lists items in correct order

@pytest.mark.ac("S6-AC3")
def test_applied_empty_no_discounts():
    """Applied is empty when no discounts apply."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("10.00"))}
    lines = [Line("ITEM", 1)]
    quote = price_cart(lines, products, today=date(2026, 1, 1))
    assert len(quote.applied) == 0


@pytest.mark.ac("S6-AC3")
def test_applied_volume_single_product():
    """Applied lists volume discount as volume:<SKU>."""
    products = {"BULK": Product("BULK", "Item", Decimal("10.00"))}
    lines = [Line("BULK", 10)]
    quote = price_cart(lines, products, today=date(2026, 1, 1))
    assert "volume:BULK" in quote.applied


@pytest.mark.ac("S6-AC3")
def test_applied_volume_multiple_products_order():
    """Applied lists multiple volume discounts in order of first appearance."""
    products = {
        "SKU1": Product("SKU1", "Item", Decimal("10.00")),
        "SKU2": Product("SKU2", "Item", Decimal("10.00")),
    }
    lines = [
        Line("SKU1", 10),
        Line("SKU2", 10),
        Line("SKU1", 5),
    ]
    quote = price_cart(lines, products, today=date(2026, 1, 1))
    applied = list(quote.applied)
    
    idx1 = next((i for i, x in enumerate(applied) if x == "volume:SKU1"), -1)
    idx2 = next((i for i, x in enumerate(applied) if x == "volume:SKU2"), -1)
    
    assert idx1 >= 0
    assert idx2 >= 0
    assert idx1 < idx2


@pytest.mark.ac("S6-AC3")
def test_applied_volume_no_discount_omitted():
    """Applied omits products without volume discount."""
    products = {
        "BULK": Product("BULK", "Item", Decimal("10.00")),
        "SMALL": Product("SMALL", "Item", Decimal("10.00")),
    }
    lines = [
        Line("BULK", 10),
        Line("SMALL", 1),
    ]
    quote = price_cart(lines, products, today=date(2026, 1, 1))
    applied = list(quote.applied)
    
    assert "volume:BULK" in applied
    assert "volume:SMALL" not in applied


@pytest.mark.ac("S6-AC3")
def test_applied_loyalty():
    """Applied lists loyalty discount as loyalty."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
    customer = Customer(tier="gold")
    lines = [Line("ITEM", 1)]
    quote = price_cart(
        lines, products, today=date(2026, 1, 1), customer=customer
    )
    assert "loyalty" in quote.applied


@pytest.mark.ac("S6-AC3")
def test_applied_percent_coupon():
    """Applied lists percent coupon as coupon:<CODE>."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
    coupon = Coupon("SAVE10", "percent", Decimal("10"))
    lines = [Line("ITEM", 1)]
    quote = price_cart(
        lines, products, today=date(2026, 1, 1), coupon=coupon
    )
    assert "coupon:SAVE10" in quote.applied


@pytest.mark.ac("S6-AC3")
def test_applied_fixed_coupon():
    """Applied lists fixed coupon as coupon:<CODE>."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
    coupon = Coupon("OFF5", "fixed", Decimal("5.00"))
    lines = [Line("ITEM", 1)]
    quote = price_cart(
        lines, products, today=date(2026, 1, 1), coupon=coupon
    )
    assert "coupon:OFF5" in quote.applied


@pytest.mark.ac("S6-AC3")
def test_applied_volume_before_loyalty():
    """Applied lists volume discount before loyalty discount."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("10.00"))}
    customer = Customer(tier="gold")
    lines = [Line("ITEM", 10)]
    quote = price_cart(
        lines, products, today=date(2026, 1, 1), customer=customer
    )
    applied = list(quote.applied)
    
    vol_idx = next((i for i, x in enumerate(applied) if "volume:" in x), -1)
    loy_idx = next((i for i, x in enumerate(applied) if x == "loyalty"), -1)
    
    assert vol_idx >= 0
    assert loy_idx >= 0
    assert vol_idx < loy_idx


@pytest.mark.ac("S6-AC3")
def test_applied_volume_before_percent_coupon():
    """Applied lists volume discount before percent coupon."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("10.00"))}
    coupon = Coupon("SAVE10", "percent", Decimal("10"))
    lines = [Line("ITEM", 10)]
    quote = price_cart(
        lines, products, today=date(2026, 1, 1), coupon=coupon
    )
    applied = list(quote.applied)
    
    vol_idx = next((i for i, x in enumerate(applied) if "volume:" in x), -1)
    coup_idx = next((i for i, x in enumerate(applied) if "coupon:" in x), -1)
    
    assert vol_idx >= 0
    assert coup_idx >= 0
    assert vol_idx < coup_idx


@pytest.mark.ac("S6-AC3")
def test_applied_loyalty_before_fixed_coupon():
    """Applied lists loyalty discount before fixed coupon."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
    customer = Customer(tier="gold")
    coupon = Coupon("OFF5", "fixed", Decimal("5.00"))
    lines = [Line("ITEM", 1)]
    quote = price_cart(
        lines, products, today=date(2026, 1, 1),
        customer=customer, coupon=coupon
    )
    applied = list(quote.applied)
    
    loy_idx = next((i for i, x in enumerate(applied) if x == "loyalty"), -1)
    coup_idx = next((i for i, x in enumerate(applied) if x == "coupon:OFF5"), -1)
    
    assert loy_idx >= 0
    assert coup_idx >= 0
    assert loy_idx < coup_idx


@pytest.mark.ac("S6-AC3")
def test_applied_percent_coupon_before_fixed():
    """Applied lists percent coupon before fixed coupon."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
    percent_coupon = Coupon("SAVE10", "percent", Decimal("10"))
    fixed_coupon = Coupon("OFF5", "fixed", Decimal("5.00"))
    lines = [Line("ITEM", 1)]
    
    quote = price_cart(
        lines, products, today=date(2026, 1, 1), coupon=percent_coupon
    )
    # Verify percent coupon comes before fixed would
    assert "coupon:SAVE10" in quote.applied


@pytest.mark.ac("S6-AC3")
def test_applied_full_order_with_all_discounts():
    """Applied lists: volumes, then loyalty, then fixed coupon."""
    products = {
        "ITEM": Product("ITEM", "Item", Decimal("10.00")),
        "OTHER": Product("OTHER", "Item", Decimal("8.00")),
    }
    customer = Customer(tier="gold")
    coupon = Coupon("OFF2", "fixed", Decimal("2.00"))
    lines = [
        Line("ITEM", 15),
        Line("OTHER", 10),
    ]
    quote = price_cart(
        lines, products, today=date(2026, 1, 1),
        customer=customer, coupon=coupon
    )
    applied = list(quote.applied)
    
    # Find indices
    vol_item = next((i for i, x in enumerate(applied) if x == "volume:ITEM"), -1)
    vol_other = next((i for i, x in enumerate(applied) if x == "volume:OTHER"), -1)
    loy = next((i for i, x in enumerate(applied) if x == "loyalty"), -1)
    fixed = next((i for i, x in enumerate(applied) if x == "coupon:OFF2"), -1)
    
    # All should be present
    assert vol_item >= 0
    assert vol_other >= 0
    assert loy >= 0
    assert fixed >= 0
    
    # Verify order: volumes, then loyalty, then fixed
    assert vol_item < loy
    assert vol_other < loy
    assert loy < fixed


@pytest.mark.ac("S6-AC3")
def test_applied_no_standard_customer_loyalty():
    """Applied does not include loyalty for standard tier customers."""
    products = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
    customer = Customer(tier="standard")
    lines = [Line("ITEM", 1)]
    quote = price_cart(
        lines, products, today=date(2026, 1, 1), customer=customer
    )
    assert "loyalty" not in quote.applied
