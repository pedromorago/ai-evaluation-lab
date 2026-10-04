import pytest
from decimal import Decimal
from datetime import date
from checkout import price_cart, Product, Line


@pytest.mark.ac("S2-AC1")
def test_volume_discount_10_units_exact():
    """10 units exactly should get 10% volume discount"""
    catalog = {
        "WIDGET": Product("WIDGET", "Widget", Decimal("10.00"), "general"),
    }
    lines = [Line("WIDGET", 10)]
    
    # Line subtotal before discount: 10 * 10.00 = 100.00
    # 10% volume discount: 100.00 * 0.10 = 10.00
    # Subtotal after discount: 100.00 - 10.00 = 90.00
    quote = price_cart(lines, catalog, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("90.00")


@pytest.mark.ac("S2-AC1")
def test_volume_discount_9_units_no_discount():
    """9 units should not get volume discount"""
    catalog = {
        "WIDGET": Product("WIDGET", "Widget", Decimal("10.00"), "general"),
    }
    lines = [Line("WIDGET", 9)]
    
    # Line subtotal: 9 * 10.00 = 90.00
    # Below 10 units, no volume discount
    # Subtotal: 90.00
    quote = price_cart(lines, catalog, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("90.00")


@pytest.mark.ac("S2-AC1")
def test_volume_discount_11_units():
    """11 units should get 10% volume discount"""
    catalog = {
        "WIDGET": Product("WIDGET", "Widget", Decimal("10.00"), "general"),
    }
    lines = [Line("WIDGET", 11)]
    
    # Line subtotal before discount: 11 * 10.00 = 110.00
    # 10% volume discount: 110.00 * 0.10 = 11.00
    # Subtotal after discount: 110.00 - 11.00 = 99.00
    quote = price_cart(lines, catalog, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("99.00")


@pytest.mark.ac("S2-AC1")
def test_volume_discount_merged_lines_10_units():
    """Merged lines with same SKU totaling 10 units should get 10% discount"""
    catalog = {
        "WIDGET": Product("WIDGET", "Widget", Decimal("10.00"), "general"),
    }
    lines = [Line("WIDGET", 7), Line("WIDGET", 3)]
    
    # Lines merged: 7 + 3 = 10 units
    # Line subtotal before discount: 10 * 10.00 = 100.00
    # 10% volume discount: 100.00 * 0.10 = 10.00
    # Subtotal after discount: 100.00 - 10.00 = 90.00
    quote = price_cart(lines, catalog, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("90.00")


@pytest.mark.ac("S2-AC1")
def test_volume_discount_merged_lines_9_units():
    """Merged lines with same SKU totaling 9 units should not get discount"""
    catalog = {
        "WIDGET": Product("WIDGET", "Widget", Decimal("10.00"), "general"),
    }
    lines = [Line("WIDGET", 5), Line("WIDGET", 4)]
    
    # Lines merged: 5 + 4 = 9 units
    # Line subtotal: 9 * 10.00 = 90.00
    # Below 10 units, no volume discount
    # Subtotal: 90.00
    quote = price_cart(lines, catalog, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("90.00")


@pytest.mark.ac("S2-AC2")
def test_volume_discount_50_units_exact():
    """50 units exactly should get 15% volume discount"""
    catalog = {
        "WIDGET": Product("WIDGET", "Widget", Decimal("10.00"), "general"),
    }
    lines = [Line("WIDGET", 50)]
    
    # Line subtotal before discount: 50 * 10.00 = 500.00
    # 15% volume discount: 500.00 * 0.15 = 75.00
    # Subtotal after discount: 500.00 - 75.00 = 425.00
    quote = price_cart(lines, catalog, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("425.00")


@pytest.mark.ac("S2-AC2")
def test_volume_discount_49_units_gets_10_percent():
    """49 units should get 10% discount, not 15%"""
    catalog = {
        "WIDGET": Product("WIDGET", "Widget", Decimal("10.00"), "general"),
    }
    lines = [Line("WIDGET", 49)]
    
    # Line subtotal before discount: 49 * 10.00 = 490.00
    # 10% volume discount (below 50 units): 490.00 * 0.10 = 49.00
    # Subtotal after discount: 490.00 - 49.00 = 441.00
    quote = price_cart(lines, catalog, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("441.00")


@pytest.mark.ac("S2-AC2")
def test_volume_discount_51_units():
    """51 units should get 15% volume discount"""
    catalog = {
        "WIDGET": Product("WIDGET", "Widget", Decimal("10.00"), "general"),
    }
    lines = [Line("WIDGET", 51)]
    
    # Line subtotal before discount: 51 * 10.00 = 510.00
    # 15% volume discount: 510.00 * 0.15 = 76.50
    # Subtotal after discount: 510.00 - 76.50 = 433.50
    quote = price_cart(lines, catalog, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("433.50")


@pytest.mark.ac("S2-AC2")
def test_volume_discount_merged_lines_50_units():
    """Merged lines totaling exactly 50 units should get 15% discount"""
    catalog = {
        "WIDGET": Product("WIDGET", "Widget", Decimal("10.00"), "general"),
    }
    lines = [Line("WIDGET", 30), Line("WIDGET", 20)]
    
    # Lines merged: 30 + 20 = 50 units
    # Line subtotal before discount: 50 * 10.00 = 500.00
    # 15% volume discount: 500.00 * 0.15 = 75.00
    # Subtotal after discount: 500.00 - 75.00 = 425.00
    quote = price_cart(lines, catalog, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("425.00")


@pytest.mark.ac("S2-AC3")
def test_no_discount_books_10_units():
    """Books with 10 units should not get volume discount"""
    catalog = {
        "BOOK": Product("BOOK", "Book", Decimal("15.00"), "books"),
    }
    lines = [Line("BOOK", 10)]
    
    # Line subtotal: 10 * 15.00 = 150.00
    # Books category never gets volume discount
    # Subtotal: 150.00
    quote = price_cart(lines, catalog, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("150.00")


@pytest.mark.ac("S2-AC3")
def test_no_discount_books_50_units():
    """Books with 50 units should not get 15% discount"""
    catalog = {
        "BOOK": Product("BOOK", "Book", Decimal("20.00"), "books"),
    }
    lines = [Line("BOOK", 50)]
    
    # Line subtotal: 50 * 20.00 = 1000.00
    # Books category never gets volume discount, even at 50+ units
    # Subtotal: 1000.00
    quote = price_cart(lines, catalog, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("1000.00")


@pytest.mark.ac("S2-AC1", "S2-AC3")
def test_general_gets_discount_books_dont():
    """General products get volume discount, books do not"""
    catalog = {
        "WIDGET": Product("WIDGET", "Widget", Decimal("10.00"), "general"),
        "BOOK": Product("BOOK", "Book", Decimal("10.00"), "books"),
    }
    lines = [Line("WIDGET", 10), Line("BOOK", 10)]
    
    # WIDGET: 10 * 10.00 = 100.00, 10% off = 10.00, line total = 90.00
    # BOOK: 10 * 10.00 = 100.00, no discount, line total = 100.00
    # Subtotal: 90.00 + 100.00 = 190.00
    quote = price_cart(lines, catalog, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("190.00")


@pytest.mark.ac("S2-AC1", "S2-AC2")
def test_multiple_products_different_discount_tiers():
    """Multiple products each reaching their own discount thresholds"""
    catalog = {
        "WIDGET": Product("WIDGET", "Widget", Decimal("10.00"), "general"),
        "GADGET": Product("GADGET", "Gadget", Decimal("5.00"), "general"),
    }
    lines = [Line("WIDGET", 10), Line("GADGET", 50)]
    
    # WIDGET: 10 * 10.00 = 100.00, 10% off = 10.00, line total = 90.00
    # GADGET: 50 * 5.00 = 250.00, 15% off = 37.50, line total = 212.50
    # Subtotal: 90.00 + 212.50 = 302.50
    quote = price_cart(lines, catalog, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("302.50")


@pytest.mark.ac("S2-AC1")
def test_volume_discount_with_fractional_unit_price():
    """Volume discount calculation with fractional prices"""
    catalog = {
        "ITEM": Product("ITEM", "Item", Decimal("12.99"), "general"),
    }
    lines = [Line("ITEM", 10)]
    
    # Line subtotal before discount: 10 * 12.99 = 129.90
    # 10% volume discount: 129.90 * 0.10 = 12.99, rounds to 12.99
    # Subtotal after discount: 129.90 - 12.99 = 116.91
    quote = price_cart(lines, catalog, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("116.91")


@pytest.mark.ac("S2-AC2")
def test_volume_discount_with_rounding_small_amounts():
    """Volume discount at 50+ units with rounding of fractional cents"""
    catalog = {
        "ITEM": Product("ITEM", "Item", Decimal("0.01"), "general"),
    }
    lines = [Line("ITEM", 50)]
    
    # Line subtotal before discount: 50 * 0.01 = 0.50
    # 15% volume discount: 0.50 * 0.15 = 0.075, rounds half-up to 0.08
    # Subtotal after discount: 0.50 - 0.08 = 0.42
    quote = price_cart(lines, catalog, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("0.42")


@pytest.mark.ac("S2-AC1", "S2-AC2", "S2-AC3")
def test_volume_discount_complex_mixed_cart():
    """Complex cart with multiple products, categories, and discount tiers"""
    catalog = {
        "WIDGET": Product("WIDGET", "Widget", Decimal("10.00"), "general"),
        "GADGET": Product("GADGET", "Gadget", Decimal("8.00"), "general"),
        "BOOK": Product("BOOK", "Book", Decimal("15.00"), "books"),
    }
    lines = [
        Line("WIDGET", 10),
        Line("GADGET", 50),
        Line("BOOK", 25),
    ]
    
    # WIDGET: 10 * 10.00 = 100.00, 10% off = 10.00, line total = 90.00
    # GADGET: 50 * 8.00 = 400.00, 15% off = 60.00, line total = 340.00
    # BOOK: 25 * 15.00 = 375.00, no discount, line total = 375.00
    # Subtotal: 90.00 + 340.00 + 375.00 = 805.00
    quote = price_cart(lines, catalog, today=date(2026, 1, 1))
    assert quote.subtotal == Decimal("805.00")
