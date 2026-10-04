import pytest
from decimal import Decimal
from datetime import date
from checkout import (
    price_cart,
    Product,
    Line,
    Customer,
    Coupon,
)


@pytest.mark.ac("S2-AC1")
def test_volume_discount_10_units_gives_10_percent():
    """10 or more units of the same product take 10% off that line"""
    catalog = {
        "WIDGET": Product(sku="WIDGET", name="Widget", unit_price=Decimal("10.00"), category="general")
    }
    lines = [Line(sku="WIDGET", quantity=10)]
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1))
    
    assert quote.subtotal == Decimal("90.00")
    assert "volume:WIDGET" in quote.applied


@pytest.mark.ac("S2-AC1")
def test_volume_discount_15_units_gives_10_percent():
    """15 units get 10% off"""
    catalog = {
        "GADGET": Product(sku="GADGET", name="Gadget", unit_price=Decimal("5.00"), category="general")
    }
    lines = [Line(sku="GADGET", quantity=15)]
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1))
    
    assert quote.subtotal == Decimal("67.50")
    assert "volume:GADGET" in quote.applied


@pytest.mark.ac("S2-AC1")
def test_volume_discount_9_units_no_discount():
    """Less than 10 units get no discount"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("10.00"), category="general")
    }
    lines = [Line(sku="ITEM", quantity=9)]
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1))
    
    assert quote.subtotal == Decimal("90.00")
    assert "volume:ITEM" not in quote.applied


@pytest.mark.ac("S2-AC2")
def test_volume_discount_50_units_gives_15_percent():
    """50 or more units take 15% off that line"""
    catalog = {
        "PRODUCT": Product(sku="PRODUCT", name="Product", unit_price=Decimal("10.00"), category="general")
    }
    lines = [Line(sku="PRODUCT", quantity=50)]
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1))
    
    assert quote.subtotal == Decimal("425.00")
    assert "volume:PRODUCT" in quote.applied


@pytest.mark.ac("S2-AC2")
def test_volume_discount_99_units_gives_15_percent():
    """99 units (max allowed) get 15% off"""
    catalog = {
        "BULKY": Product(sku="BULKY", name="Bulky", unit_price=Decimal("2.00"), category="general")
    }
    lines = [Line(sku="BULKY", quantity=99)]
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1))
    
    assert quote.subtotal == Decimal("168.30")
    assert "volume:BULKY" in quote.applied


@pytest.mark.ac("S2-AC2")
def test_volume_discount_49_units_gives_10_percent():
    """49 units get only 10% off (below 50 threshold)"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("10.00"), category="general")
    }
    lines = [Line(sku="ITEM", quantity=49)]
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1))
    
    assert quote.subtotal == Decimal("441.00")
    assert "volume:ITEM" in quote.applied


@pytest.mark.ac("S2-AC3")
def test_volume_discount_books_never_discounted_at_50_units():
    """Products in the books category never get a volume discount"""
    catalog = {
        "BOOK123": Product(sku="BOOK123", name="Book", unit_price=Decimal("20.00"), category="books")
    }
    lines = [Line(sku="BOOK123", quantity=50)]
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1))
    
    assert quote.subtotal == Decimal("1000.00")
    assert "volume:BOOK123" not in quote.applied


@pytest.mark.ac("S2-AC3")
def test_volume_discount_books_never_discounted_at_10_units():
    """10 units of a book product still gets no discount"""
    catalog = {
        "BOOK456": Product(sku="BOOK456", name="Another Book", unit_price=Decimal("15.00"), category="books")
    }
    lines = [Line(sku="BOOK456", quantity=10)]
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1))
    
    assert quote.subtotal == Decimal("150.00")
    assert "volume:BOOK456" not in quote.applied


@pytest.mark.ac("S1-AC4", "S2-AC1")
def test_volume_discount_after_merging_lines_to_10():
    """Lines with the same SKU are merged before volume discount check"""
    catalog = {
        "WIDGET": Product(sku="WIDGET", name="Widget", unit_price=Decimal("10.00"), category="general")
    }
    lines = [
        Line(sku="WIDGET", quantity=7),
        Line(sku="WIDGET", quantity=5)
    ]
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1))
    
    assert quote.subtotal == Decimal("108.00")
    assert "volume:WIDGET" in quote.applied


@pytest.mark.ac("S1-AC4", "S2-AC2")
def test_volume_discount_after_merging_lines_to_50():
    """Merging lines that total 50+ gets 15% discount"""
    catalog = {
        "GADGET": Product(sku="GADGET", name="Gadget", unit_price=Decimal("5.00"), category="general")
    }
    lines = [
        Line(sku="GADGET", quantity=30),
        Line(sku="GADGET", quantity=20)
    ]
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1))
    
    assert quote.subtotal == Decimal("212.50")
    assert "volume:GADGET" in quote.applied


@pytest.mark.ac("S2-AC1", "S2-AC2", "S2-AC3")
def test_volume_discount_multiple_products():
    """Multiple products in cart each get their own volume discount"""
    catalog = {
        "WIDGET": Product(sku="WIDGET", name="Widget", unit_price=Decimal("10.00"), category="general"),
        "GADGET": Product(sku="GADGET", name="Gadget", unit_price=Decimal("5.00"), category="general"),
        "BOOK": Product(sku="BOOK", name="Book", unit_price=Decimal("20.00"), category="books")
    }
    lines = [
        Line(sku="WIDGET", quantity=15),
        Line(sku="GADGET", quantity=60),
        Line(sku="BOOK", quantity=25)
    ]
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1))
    
    assert quote.subtotal == Decimal("890.00")
    assert "volume:WIDGET" in quote.applied
    assert "volume:GADGET" in quote.applied
    assert "volume:BOOK" not in quote.applied


@pytest.mark.ac("S1-AC5", "S2-AC1")
def test_volume_discount_empty_cart():
    """Empty cart has no volume discounts applied"""
    catalog = {
        "WIDGET": Product(sku="WIDGET", name="Widget", unit_price=Decimal("10.00"), category="general")
    }
    lines = []
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1))
    
    assert quote.subtotal == Decimal("0.00")
    assert quote.applied == ()


@pytest.mark.ac("S2-AC1", "S6-AC2")
def test_volume_discount_rounding():
    """Volume discount is rounded half-up to the cent"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("3.33"), category="general")
    }
    lines = [Line(sku="ITEM", quantity=10)]
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1))
    
    assert quote.subtotal == Decimal("29.97")
    assert "volume:ITEM" in quote.applied


@pytest.mark.ac("S2-AC1", "S6-AC3")
def test_volume_discount_applied_order():
    """Volume discounts appear in applied in order products first appear"""
    catalog = {
        "WIDGET": Product(sku="WIDGET", name="Widget", unit_price=Decimal("10.00"), category="general"),
        "GADGET": Product(sku="GADGET", name="Gadget", unit_price=Decimal("5.00"), category="general"),
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("2.00"), category="general")
    }
    lines = [
        Line(sku="WIDGET", quantity=10),
        Line(sku="GADGET", quantity=50),
        Line(sku="ITEM", quantity=15)
    ]
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1))
    
    applied_list = quote.applied
    widget_idx = applied_list.index("volume:WIDGET")
    gadget_idx = applied_list.index("volume:GADGET")
    item_idx = applied_list.index("volume:ITEM")
    assert widget_idx < gadget_idx < item_idx


@pytest.mark.ac("S2-AC1", "S4-AC2")
def test_volume_discount_with_loyalty():
    """Volume discount applied to subtotal before loyalty discount"""
    catalog = {
        "WIDGET": Product(sku="WIDGET", name="Widget", unit_price=Decimal("10.00"), category="general")
    }
    lines = [Line(sku="WIDGET", quantity=10)]
    customer = Customer(tier="gold")
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1), customer=customer)
    
    assert quote.subtotal == Decimal("90.00")
    assert "volume:WIDGET" in quote.applied


@pytest.mark.ac("S2-AC1", "S3-AC1")
def test_volume_discount_with_percent_coupon():
    """Volume discount applied before percent coupon"""
    catalog = {
        "WIDGET": Product(sku="WIDGET", name="Widget", unit_price=Decimal("10.00"), category="general")
    }
    lines = [Line(sku="WIDGET", quantity=10)]
    coupon = Coupon(code="SAVE10", kind="percent", value=Decimal("10"))
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1), coupon=coupon)
    
    assert quote.subtotal == Decimal("90.00")
    assert "volume:WIDGET" in quote.applied


@pytest.mark.ac("S2-AC1")
def test_volume_discount_with_varying_prices():
    """Volume discount percentage applied correctly for different unit prices"""
    catalog = {
        "EXPENSIVE": Product(sku="EXPENSIVE", name="Expensive", unit_price=Decimal("100.00"), category="general"),
        "CHEAP": Product(sku="CHEAP", name="Cheap", unit_price=Decimal("1.00"), category="general")
    }
    lines = [
        Line(sku="EXPENSIVE", quantity=10),
        Line(sku="CHEAP", quantity=10)
    ]
    
    quote = price_cart(lines=lines, catalog=catalog, today=date(2026, 1, 1))
    
    assert quote.subtotal == Decimal("909.00")
    assert "volume:EXPENSIVE" in quote.applied
    assert "volume:CHEAP" in quote.applied
