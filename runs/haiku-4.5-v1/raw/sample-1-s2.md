```python
import pytest
from decimal import Decimal
from datetime import date
from checkout import price_cart, Product, Line


@pytest.fixture
def today():
    return date(2024, 1, 1)


@pytest.fixture
def catalog():
    return {
        "SKU-001": Product(sku="SKU-001", name="Widget", unit_price=Decimal("10.00"), category="general"),
        "SKU-002": Product(sku="SKU-002", name="Book", unit_price=Decimal("20.00"), category="books"),
        "SKU-003": Product(sku="SKU-003", name="Gadget", unit_price=Decimal("1.00"), category="general"),
    }


@pytest.mark.ac("S2-AC1")
def test_volume_discount_exactly_10_units(catalog, today):
    """10 or more units of the same product take 10% off that line."""
    lines = [Line(sku="SKU-001", quantity=10)]
    quote = price_cart(lines, catalog, today=today)
    assert quote.subtotal == Decimal("90.00")
    assert "volume:SKU-001" in quote.applied


@pytest.mark.ac("S2-AC1")
def test_volume_discount_more_than_10_units(catalog, today):
    """More than 10 units also gets 10% discount."""
    lines = [Line(sku="SKU-001", quantity=11)]
    quote = price_cart(lines, catalog, today=today)
    assert quote.subtotal == Decimal("99.00")
    assert "volume:SKU-001" in quote.applied


@pytest.mark.ac("S2-AC1")
def test_no_volume_discount_less_than_10_units(catalog, today):
    """Less than 10 units does not get volume discount."""
    lines = [Line(sku="SKU-003", quantity=9)]
    quote = price_cart(lines, catalog, today=today)
    assert quote.subtotal == Decimal("9.00")
    assert "volume:SKU-003" not in quote.applied


@pytest.mark.ac("S2-AC2")
def test_volume_discount_exactly_50_units(catalog, today):
    """50 or more units take 15% off that line instead."""
    lines = [Line(sku="SKU-003", quantity=50)]
    quote = price_cart(lines, catalog, today=today)
    assert quote.subtotal == Decimal("42.50")
    assert "volume:SKU-003" in quote.applied


@pytest.mark.ac("S2-AC2")
def test_volume_discount_more_than_50_units(catalog, today):
    """More than 50 units also gets 15% discount."""
    lines = [Line(sku="SKU-003", quantity=51)]
    quote = price_cart(lines, catalog, today=today)
    assert quote.subtotal == Decimal("43.35")
    assert "volume:SKU-003" in quote.applied


@pytest.mark.ac("S2-AC2")
def test_volume_discount_49_units_gets_10_percent(catalog, today):
    """49 units gets 10% discount, not 15%."""
    lines = [Line(sku="SKU-003", quantity=49)]
    quote = price_cart(lines, catalog, today=today)
    assert quote.subtotal == Decimal("44.10")
    assert "volume:SKU-003" in quote.applied


@pytest.mark.ac("S2-AC3")
def test_no_volume_discount_for_books_category_10_units(catalog, today):
    """Products in the books category never get a volume discount."""
    lines = [Line(sku="SKU-002", quantity=10)]
    quote = price_cart(lines, catalog, today=today)
    assert quote.subtotal == Decimal("200.00")
    assert "volume:SKU-002" not in quote.applied


@pytest.mark.ac("S2-AC3")
def test_no_volume_discount_for_books_category_50_units(catalog, today):
    """Books category with 50+ units still doesn't get volume discount."""
    lines = [Line(sku="SKU-002", quantity=50)]
    quote = price_cart(lines, catalog, today=today)
    assert quote.subtotal == Decimal("1000.00")
    assert "volume:SKU-002" not in quote.applied


@pytest.mark.ac("S2-AC1")
def test_volume_discount_with_merged_lines_10_units(catalog, today):
    """Volume discount is applied after merging lines with the same SKU."""
    lines = [
        Line(sku="SKU-001", quantity=6),
        Line(sku="SKU-001", quantity=4),
    ]
    quote = price_cart(lines, catalog, today=today)
    assert quote.subtotal == Decimal("90.00")
    assert "volume:SKU-001" in quote.applied


@pytest.mark.ac("S2-AC2")
def test_volume_discount_with_merged_lines_50_units(catalog, today):
    """Volume discount is applied after merging lines with the same SKU (50+ units)."""
    lines = [
        Line(sku="SKU-003", quantity=30),
        Line(sku="SKU-003", quantity=20),
    ]
    quote = price_cart(lines, catalog, today=today)
    assert quote.subtotal == Decimal("42.50")
    assert "volume:SKU-003" in quote.applied


@pytest.mark.ac("S2-AC1", "S2-AC2")
def test_volume_discount_multiple_products(catalog, today):
    """Different products with volume discounts are all discounted."""
    lines = [
        Line(sku="SKU-001", quantity=10),
        Line(sku="SKU-003", quantity=50),
    ]
    quote = price_cart(lines, catalog, today=today)
    assert quote.subtotal == Decimal("132.50")
    assert "volume:SKU-001" in quote.applied
    assert "volume:SKU-003" in quote.applied
    assert quote.applied.index("volume:SKU-001") < quote.applied.index("volume:SKU-003")


@pytest.mark.ac("S2-AC1", "S2-AC3")
def test_volume_discount_mixed_with_books(catalog, today):
    """Mix of products with and without volume discounts."""
    lines = [
        Line(sku="SKU-001", quantity=10),
        Line(sku="SKU-002", quantity=10),
    ]
    quote = price_cart(lines, catalog, today=today)
    assert quote.subtotal == Decimal("290.00")
    assert "volume:SKU-001" in quote.applied
    assert "volume:SKU-002" not in quote.applied
```