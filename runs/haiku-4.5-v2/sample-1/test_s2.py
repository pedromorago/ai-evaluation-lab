import pytest
from datetime import date
from decimal import Decimal
from checkout import Product, Line, price_cart

TODAY = date(2026, 10, 3)


# S2-AC1: 10 or more units get 10% off


@pytest.mark.ac("S2-AC1")
def test_volume_discount_exactly_10_units():
    """10 units of same product get 10% discount"""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Widget", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=10)]
    
    # Line total: 10.00 * 10 = 100.00
    # Volume discount (10%): 100.00 * 0.10 = 10.00
    # Subtotal: 100.00 - 10.00 = 90.00
    quote = price_cart(lines, catalog, today=TODAY)
    assert quote.subtotal == Decimal("90.00")
    assert "volume:SKU-1" in quote.applied


@pytest.mark.ac("S2-AC1")
def test_no_volume_discount_at_9_units():
    """9 units do not qualify for volume discount"""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Widget", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=9)]
    
    # Line total: 10.00 * 9 = 90.00
    # No volume discount (below 10)
    # Subtotal: 90.00
    quote = price_cart(lines, catalog, today=TODAY)
    assert quote.subtotal == Decimal("90.00")
    assert "volume:SKU-1" not in quote.applied


@pytest.mark.ac("S2-AC1")
def test_volume_discount_at_11_units():
    """11 units get 10% discount"""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Widget", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=11)]
    
    # Line total: 10.00 * 11 = 110.00
    # Volume discount (10%): 110.00 * 0.10 = 11.00
    # Subtotal: 110.00 - 11.00 = 99.00
    quote = price_cart(lines, catalog, today=TODAY)
    assert quote.subtotal == Decimal("99.00")
    assert "volume:SKU-1" in quote.applied


@pytest.mark.ac("S2-AC1")
def test_merged_lines_reach_10_units_threshold():
    """Lines with same SKU merge; discount applies to merged quantity"""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Widget", unit_price=Decimal("10.00"))}
    lines = [
        Line(sku="SKU-1", quantity=6),
        Line(sku="SKU-1", quantity=4),
    ]
    
    # Merged quantity: 6 + 4 = 10
    # Line total: 10.00 * 10 = 100.00
    # Volume discount (10%): 100.00 * 0.10 = 10.00
    # Subtotal: 100.00 - 10.00 = 90.00
    quote = price_cart(lines, catalog, today=TODAY)
    assert quote.subtotal == Decimal("90.00")
    assert "volume:SKU-1" in quote.applied


@pytest.mark.ac("S2-AC1")
def test_merged_lines_below_10_units_no_discount():
    """Merged lines below 10 units do not get volume discount"""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Widget", unit_price=Decimal("10.00"))}
    lines = [
        Line(sku="SKU-1", quantity=5),
        Line(sku="SKU-1", quantity=4),
    ]
    
    # Merged quantity: 5 + 4 = 9
    # Line total: 10.00 * 9 = 90.00
    # No volume discount
    # Subtotal: 90.00
    quote = price_cart(lines, catalog, today=TODAY)
    assert quote.subtotal == Decimal("90.00")
    assert "volume:SKU-1" not in quote.applied


# S2-AC2: 50 or more units get 15% off


@pytest.mark.ac("S2-AC2")
def test_volume_discount_49_units_gets_10_percent_not_15():
    """49 units get 10% discount, not 15%"""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Widget", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=49)]
    
    # Line total: 10.00 * 49 = 490.00
    # Volume discount (10%): 490.00 * 0.10 = 49.00
    # Subtotal: 490.00 - 49.00 = 441.00
    quote = price_cart(lines, catalog, today=TODAY)
    assert quote.subtotal == Decimal("441.00")
    assert "volume:SKU-1" in quote.applied


@pytest.mark.ac("S2-AC2")
def test_volume_discount_exactly_50_units_gets_15_percent():
    """Exactly 50 units get 15% discount"""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Widget", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=50)]
    
    # Line total: 10.00 * 50 = 500.00
    # Volume discount (15%): 500.00 * 0.15 = 75.00
    # Subtotal: 500.00 - 75.00 = 425.00
    quote = price_cart(lines, catalog, today=TODAY)
    assert quote.subtotal == Decimal("425.00")
    assert "volume:SKU-1" in quote.applied


@pytest.mark.ac("S2-AC2")
def test_volume_discount_51_units_gets_15_percent():
    """51 units get 15% discount"""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Widget", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=51)]
    
    # Line total: 10.00 * 51 = 510.00
    # Volume discount (15%): 510.00 * 0.15 = 76.50
    # Subtotal: 510.00 - 76.50 = 433.50
    quote = price_cart(lines, catalog, today=TODAY)
    assert quote.subtotal == Decimal("433.50")
    assert "volume:SKU-1" in quote.applied


# S2-AC3: Books category never get volume discount


@pytest.mark.ac("S2-AC3")
def test_books_never_get_volume_discount_at_10_units():
    """Books category never gets volume discount, even at 10 units"""
    catalog = {
        "BOOK-1": Product(
            sku="BOOK-1",
            name="Textbook",
            unit_price=Decimal("20.00"),
            category="books",
        )
    }
    lines = [Line(sku="BOOK-1", quantity=10)]
    
    # Line total: 20.00 * 10 = 200.00
    # No volume discount (books category)
    # Subtotal: 200.00
    quote = price_cart(lines, catalog, today=TODAY)
    assert quote.subtotal == Decimal("200.00")
    assert "volume:BOOK-1" not in quote.applied


@pytest.mark.ac("S2-AC3")
def test_books_never_get_volume_discount_at_50_units():
    """Books category never gets volume discount, even at 50 units"""
    catalog = {
        "BOOK-1": Product(
            sku="BOOK-1",
            name="Textbook",
            unit_price=Decimal("20.00"),
            category="books",
        )
    }
    lines = [Line(sku="BOOK-1", quantity=50)]
    
    # Line total: 20.00 * 50 = 1000.00
    # No volume discount (books category)
    # Subtotal: 1000.00
    quote = price_cart(lines, catalog, today=TODAY)
    assert quote.subtotal == Decimal("1000.00")
    assert "volume:BOOK-1" not in quote.applied


@pytest.mark.ac("S2-AC1", "S2-AC3")
def test_general_category_gets_discount_but_books_do_not():
    """General category products get volume discount but books do not"""
    catalog = {
        "GADGET": Product(
            sku="GADGET",
            name="Gadget",
            unit_price=Decimal("10.00"),
            category="general",
        ),
        "BOOK-1": Product(
            sku="BOOK-1", name="Book", unit_price=Decimal("10.00"), category="books"
        ),
    }
    lines = [
        Line(sku="GADGET", quantity=10),
        Line(sku="BOOK-1", quantity=10),
    ]
    
    # GADGET: 10.00 * 10 = 100.00, discount 10% = 10.00, after discount: 90.00
    # BOOK-1: 10.00 * 10 = 100.00, no discount, after discount: 100.00
    # Subtotal: 90.00 + 100.00 = 190.00
    quote = price_cart(lines, catalog, today=TODAY)
    assert quote.subtotal == Decimal("190.00")
    assert "volume:GADGET" in quote.applied
    assert "volume:BOOK-1" not in quote.applied


# Multiple products and order tests


@pytest.mark.ac("S2-AC1", "S2-AC2")
def test_multiple_products_different_discount_tiers():
    """Multiple products can each get different volume discount tiers"""
    catalog = {
        "GADGET": Product(sku="GADGET", name="Gadget", unit_price=Decimal("10.00")),
        "WIDGET": Product(sku="WIDGET", name="Widget", unit_price=Decimal("10.00")),
    }
    lines = [
        Line(sku="GADGET", quantity=10),
        Line(sku="WIDGET", quantity=50),
    ]
    
    # GADGET: 10.00 * 10 = 100.00, discount 10% = 10.00, after: 90.00
    # WIDGET: 10.00 * 50 = 500.00, discount 15% = 75.00, after: 425.00
    # Subtotal: 90.00 + 425.00 = 515.00
    quote = price_cart(lines, catalog, today=TODAY)
    assert quote.subtotal == Decimal("515.00")
    assert "volume:GADGET" in quote.applied
    assert "volume:WIDGET" in quote.applied


@pytest.mark.ac("S2-AC1", "S2-AC2")
def test_volume_discounts_in_applied_list_follow_cart_order():
    """Volume discount entries in applied list appear in cart order"""
    catalog = {
        "WIDGET": Product(sku="WIDGET", name="Widget", unit_price=Decimal("10.00")),
        "GADGET": Product(sku="GADGET", name="Gadget", unit_price=Decimal("10.00")),
    }
    lines = [
        Line(sku="WIDGET", quantity=50),
        Line(sku="GADGET", quantity=10),
    ]
    
    quote = price_cart(lines, catalog, today=TODAY)
    applied_list = list(quote.applied)
    widget_idx = next(i for i, v in enumerate(applied_list) if v == "volume:WIDGET")
    gadget_idx = next(i for i, v in enumerate(applied_list) if v == "volume:GADGET")
    # WIDGET appears first in cart, so must come first in applied
    assert widget_idx < gadget_idx


# Rounding and decimal precision tests


@pytest.mark.ac("S2-AC1")
def test_volume_discount_with_decimal_unit_price():
    """Volume discount computed correctly with decimal unit prices"""
    catalog = {
        "SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("9.99"))
    }
    lines = [Line(sku="SKU-1", quantity=10)]
    
    # Line total: 9.99 * 10 = 99.90
    # Volume discount (10%): 99.90 * 0.10 = 9.99
    # Subtotal: 99.90 - 9.99 = 89.91
    quote = price_cart(lines, catalog, today=TODAY)
    assert quote.subtotal == Decimal("89.91")
    assert "volume:SKU-1" in quote.applied


@pytest.mark.ac("S2-AC1")
def test_volume_discount_10_percent_with_rounding():
    """10% discount amount is rounded correctly"""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("3.33"))}
    lines = [Line(sku="SKU-1", quantity=10)]
    
    # Line total: 3.33 * 10 = 33.30
    # Volume discount (10%): 33.30 * 0.10 = 3.33
    # Subtotal: 33.30 - 3.33 = 29.97
    quote = price_cart(lines, catalog, today=TODAY)
    assert quote.subtotal == Decimal("29.97")
    assert "volume:SKU-1" in quote.applied


@pytest.mark.ac("S2-AC2")
def test_volume_discount_15_percent_with_rounding():
    """15% discount amount is rounded correctly"""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("1.00"))}
    lines = [Line(sku="SKU-1", quantity=50)]
    
    # Line total: 1.00 * 50 = 50.00
    # Volume discount (15%): 50.00 * 0.15 = 7.50
    # Subtotal: 50.00 - 7.50 = 42.50
    quote = price_cart(lines, catalog, today=TODAY)
    assert quote.subtotal == Decimal("42.50")
    assert "volume:SKU-1" in quote.applied
