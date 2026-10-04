```python
import pytest
from datetime import date
from decimal import Decimal
from checkout import price_cart, CartError, Product, Line, Customer, Coupon


# S1-AC1: Line pricing
@pytest.mark.ac("S1-AC1")
def test_single_line_basic_pricing():
    """Each line costs unit_price × quantity"""
    products = {
        "SKU-1": Product(sku="SKU-1", name="Item 1", unit_price=Decimal("10.00"))
    }
    lines = [Line(sku="SKU-1", quantity=3)]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    # 10.00 × 3 = 30.00
    assert quote.subtotal == Decimal("30.00")


@pytest.mark.ac("S1-AC1")
def test_multiple_lines_summed():
    """Subtotal is sum of all line totals"""
    products = {
        "SKU-1": Product(sku="SKU-1", name="Item 1", unit_price=Decimal("10.00")),
        "SKU-2": Product(sku="SKU-2", name="Item 2", unit_price=Decimal("20.00"))
    }
    lines = [
        Line(sku="SKU-1", quantity=2),
        Line(sku="SKU-2", quantity=3)
    ]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    # (10.00 × 2) + (20.00 × 3) = 20.00 + 60.00 = 80.00
    assert quote.subtotal == Decimal("80.00")


@pytest.mark.ac("S1-AC1")
def test_decimal_unit_prices():
    """Line pricing works with decimal unit prices"""
    products = {
        "SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("7.50"))
    }
    lines = [Line(sku="SKU-1", quantity=4)]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    # 7.50 × 4 = 30.00
    assert quote.subtotal == Decimal("30.00")


@pytest.mark.ac("S1-AC1")
def test_volume_discount_below_10_units():
    """No volume discount below 10 units"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=9)]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    # 10.00 × 9 = 90.00 (no discount at 9 units)
    assert quote.subtotal == Decimal("90.00")


@pytest.mark.ac("S1-AC1")
def test_volume_discount_10_percent_at_10_units():
    """10% volume discount at exactly 10 units"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=10)]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    # 10.00 × 10 = 100.00, minus 10% = 90.00
    assert quote.subtotal == Decimal("90.00")


@pytest.mark.ac("S1-AC1")
def test_volume_discount_10_percent_at_49_units():
    """10% volume discount at 49 units (below 50 threshold)"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=49)]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    # 10.00 × 49 = 490.00, minus 10% = 441.00
    assert quote.subtotal == Decimal("441.00")


@pytest.mark.ac("S1-AC1")
def test_volume_discount_15_percent_at_50_units():
    """15% volume discount at exactly 50 units"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=50)]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    # 10.00 × 50 = 500.00, minus 15% = 425.00
    assert quote.subtotal == Decimal("425.00")


@pytest.mark.ac("S1-AC1")
def test_books_category_no_volume_discount():
    """Books category never receives volume discount"""
    products = {
        "BK-001": Product(sku="BK-001", name="Book", unit_price=Decimal("15.00"), category="books")
    }
    lines = [Line(sku="BK-001", quantity=50)]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    # 15.00 × 50 = 750.00 (no discount for books category)
    assert quote.subtotal == Decimal("750.00")


@pytest.mark.ac("S1-AC1")
def test_multiple_products_different_discounts():
    """Multiple products at different volume discount levels"""
    products = {
        "SKU-1": Product(sku="SKU-1", name="Item 1", unit_price=Decimal("10.00")),
        "SKU-2": Product(sku="SKU-2", name="Item 2", unit_price=Decimal("20.00"))
    }
    lines = [
        Line(sku="SKU-1", quantity=5),
        Line(sku="SKU-2", quantity=10)
    ]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    # SKU-1: 10.00 × 5 = 50.00 (no discount)
    # SKU-2: 20.00 × 10 = 200.00, minus 10% = 180.00
    # Subtotal = 50.00 + 180.00 = 230.00
    assert quote.subtotal == Decimal("230.00")


# S1-AC2: Quantity validation
@pytest.mark.ac("S1-AC2")
def test_quantity_zero_raises_error():
    """Quantity of 0 raises CartError"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10"))}
    lines = [Line(sku="SKU-1", quantity=0)]
    with pytest.raises(CartError):
        price_cart(lines, products, today=date(2026, 10, 3))


@pytest.mark.ac("S1-AC2")
def test_quantity_negative_raises_error():
    """Negative quantity raises CartError"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10"))}
    lines = [Line(sku="SKU-1", quantity=-1)]
    with pytest.raises(CartError):
        price_cart(lines, products, today=date(2026, 10, 3))


@pytest.mark.ac("S1-AC2")
def test_quantity_100_raises_error():
    """Quantity of 100 raises CartError"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10"))}
    lines = [Line(sku="SKU-1", quantity=100)]
    with pytest.raises(CartError):
        price_cart(lines, products, today=date(2026, 10, 3))


@pytest.mark.ac("S1-AC2")
def test_quantity_1_valid():
    """Quantity of 1 is valid"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10"))}
    lines = [Line(sku="SKU-1", quantity=1)]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    assert quote.subtotal == Decimal("10")


@pytest.mark.ac("S1-AC2")
def test_quantity_99_valid():
    """Quantity of 99 is valid"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10"))}
    lines = [Line(sku="SKU-1", quantity=99)]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    # 10 × 99 = 990, minus 15% = 841.50
    assert quote.subtotal == Decimal("841.50")


@pytest.mark.ac("S1-AC2")
def test_quantity_fraction_raises_error():
    """Fractional quantity raises CartError"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10"))}
    lines = [Line(sku="SKU-1", quantity=2.5)]
    with pytest.raises(CartError):
        price_cart(lines, products, today=date(2026, 10, 3))


@pytest.mark.ac("S1-AC2")
def test_quantity_true_raises_error():
    """Quantity of True raises CartError"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10"))}
    lines = [Line(sku="SKU-1", quantity=True)]
    with pytest.raises(CartError):
        price_cart(lines, products, today=date(2026, 10, 3))


# S1-AC3: SKU validation
@pytest.mark.ac("S1-AC3")
def test_unknown_sku_raises_error():
    """SKU not in catalog raises CartError"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10"))}
    lines = [Line(sku="UNKNOWN", quantity=5)]
    with pytest.raises(CartError):
        price_cart(lines, products, today=date(2026, 10, 3))


@pytest.mark.ac("S1-AC3")
def test_known_sku_valid():
    """SKU in catalog is accepted"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10"))}
    lines = [Line(sku="SKU-1", quantity=5)]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    assert quote.subtotal == Decimal("50")


# S1-AC4: Line merging
@pytest.mark.ac("S1-AC4")
def test_merge_two_lines_same_sku():
    """Lines with same SKU are merged"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10"))}
    lines = [
        Line(sku="SKU-1", quantity=3),
        Line(sku="SKU-1", quantity=5)
    ]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    # Merged: 3 + 5 = 8, 10 × 8 = 80 (no discount)
    assert quote.subtotal == Decimal("80")


@pytest.mark.ac("S1-AC4")
def test_merge_three_lines_same_sku():
    """Three lines with same SKU are merged"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10"))}
    lines = [
        Line(sku="SKU-1", quantity=20),
        Line(sku="SKU-1", quantity=15),
        Line(sku="SKU-1", quantity=10)
    ]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    # Merged: 20 + 15 + 10 = 45, 10 × 45 = 450, minus 10% = 405
    assert quote.subtotal == Decimal("405")


@pytest.mark.ac("S1-AC4")
def test_merge_below_volume_threshold():
    """Merged quantity below 10 units has no volume discount"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10"))}
    lines = [
        Line(sku="SKU-1", quantity=4),
        Line(sku="SKU-1", quantity=5)
    ]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    # Merged: 4 + 5 = 9, 10 × 9 = 90 (no discount)
    assert quote.subtotal == Decimal("90")


@pytest.mark.ac("S1-AC4")
def test_merge_activates_volume_discount():
    """Merging lines can activate volume discount"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10"))}
    lines = [
        Line(sku="SKU-1", quantity=7),
        Line(sku="SKU-1", quantity=3)
    ]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    # Merged: 7 + 3 = 10, 10 × 10 = 100, minus 10% = 90
    assert quote.subtotal == Decimal("90")


@pytest.mark.ac("S1-AC4")
def test_merge_quantity_99_valid():
    """Merged quantity of exactly 99 is valid"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10"))}
    lines = [
        Line(sku="SKU-1", quantity=50),
        Line(sku="SKU-1", quantity=49)
    ]
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    # Merged: 50 + 49 = 99, 10 × 99 = 990, minus 15% = 841.50
    assert quote.subtotal == Decimal("841.50")


@pytest.mark.ac("S1-AC4")
def test_merge_quantity_100_raises_error():
    """Merged quantity of 100 raises CartError"""
    products = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10"))}
    lines = [
        Line(sku="SKU-1", quantity=50),
        Line(sku="SKU-1", quantity=50)
    ]
    with pytest.raises(CartError):
        price_cart(lines, products, today=date(2026, 10, 3))


# S1-AC5: Empty cart
@pytest.mark.ac("S1-AC5")
def test_empty_cart_all_amounts_zero():
    """Empty cart: all amounts are 0.00"""
    products = {}
    lines = []
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    assert quote.subtotal == Decimal("0.00")
    assert quote.discount == Decimal("0.00")
    assert quote.shipping == Decimal("0.00")
    assert quote.tax == Decimal("0.00")
    assert quote.total == Decimal("0.00")


@pytest.mark.ac("S1-AC5")
def test_empty_cart_applied_empty():
    """Empty cart: applied tuple is empty"""
    products = {}
    lines = []
    quote = price_cart(lines, products, today=date(2026, 10, 3))
    assert quote.applied == ()


@pytest.mark.ac("S1-AC5")
def test_empty_cart_ignores_coupon():
    """Empty cart: coupon is ignored"""
    products = {}
    lines = []
    coupon = Coupon(code="SAVE10", kind="percent", value=Decimal("10"))
    quote = price_cart(lines, products, today=date(2026, 10, 3), coupon=coupon)
    assert quote.total == Decimal("0.00")
    assert len(quote.applied) == 0


@pytest.mark.ac("S1-AC5")
def test_empty_cart_ignores_loyalty_tier():
    """Empty cart: loyalty tier is ignored"""
    products = {}
    lines = []
    customer = Customer(tier="gold")
    quote = price_cart(lines, products, today=date(2026, 10, 3), customer=customer)
    assert quote.total == Decimal("0.00")
    assert "loyalty" not in quote.applied
```