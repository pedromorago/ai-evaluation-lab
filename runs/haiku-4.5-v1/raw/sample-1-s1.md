```python
import pytest
from decimal import Decimal
from datetime import date
from checkout import CartError, Product, Line, Customer, Coupon, price_cart


# S1-AC1: Line costs and subtotal
@pytest.mark.ac("S1-AC1")
def test_ac1_single_line_cost():
    """Each line costs unit_price * quantity"""
    catalog = {"SKU1": Product(sku="SKU1", name="Product 1", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU1", quantity=5)]
    quote = price_cart(lines, catalog, today=date(2026, 10, 3))
    assert quote.subtotal == Decimal("50.00")


@pytest.mark.ac("S1-AC1")
def test_ac1_multiple_lines():
    """Subtotal is sum of all line totals"""
    catalog = {
        "SKU1": Product(sku="SKU1", name="Product 1", unit_price=Decimal("10.00")),
        "SKU2": Product(sku="SKU2", name="Product 2", unit_price=Decimal("20.00")),
    }
    lines = [Line(sku="SKU1", quantity=2), Line(sku="SKU2", quantity=3)]
    quote = price_cart(lines, catalog, today=date(2026, 10, 3))
    assert quote.subtotal == Decimal("80.00")


# S1-AC2: Quantity validation
@pytest.mark.ac("S1-AC2")
def test_ac2_quantity_zero():
    """Quantity of 0 raises CartError"""
    catalog = {"SKU1": Product(sku="SKU1", name="Product 1", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU1", quantity=0)]
    with pytest.raises(CartError):
        price_cart(lines, catalog, today=date(2026, 10, 3))


@pytest.mark.ac("S1-AC2")
def test_ac2_quantity_negative():
    """Negative quantity raises CartError"""
    catalog = {"SKU1": Product(sku="SKU1", name="Product 1", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU1", quantity=-5)]
    with pytest.raises(CartError):
        price_cart(lines, catalog, today=date(2026, 10, 3))


@pytest.mark.ac("S1-AC2")
def test_ac2_quantity_100():
    """Quantity of 100 raises CartError"""
    catalog = {"SKU1": Product(sku="SKU1", name="Product 1", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU1", quantity=100)]
    with pytest.raises(CartError):
        price_cart(lines, catalog, today=date(2026, 10, 3))


@pytest.mark.ac("S1-AC2")
def test_ac2_quantity_over_100():
    """Quantity over 100 raises CartError"""
    catalog = {"SKU1": Product(sku="SKU1", name="Product 1", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU1", quantity=150)]
    with pytest.raises(CartError):
        price_cart(lines, catalog, today=date(2026, 10, 3))


@pytest.mark.ac("S1-AC2")
def test_ac2_quantity_float():
    """Quantity of 2.5 (fraction) raises CartError"""
    catalog = {"SKU1": Product(sku="SKU1", name="Product 1", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU1", quantity=2.5)]
    with pytest.raises(CartError):
        price_cart(lines, catalog, today=date(2026, 10, 3))


@pytest.mark.ac("S1-AC2")
def test_ac2_quantity_true():
    """Quantity of True raises CartError"""
    catalog = {"SKU1": Product(sku="SKU1", name="Product 1", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU1", quantity=True)]
    with pytest.raises(CartError):
        price_cart(lines, catalog, today=date(2026, 10, 3))


@pytest.mark.ac("S1-AC2")
def test_ac2_quantity_valid_boundary_one():
    """Quantity of 1 is valid"""
    catalog = {"SKU1": Product(sku="SKU1", name="Product 1", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU1", quantity=1)]
    quote = price_cart(lines, catalog, today=date(2026, 10, 3))
    assert quote.subtotal == Decimal("10.00")


@pytest.mark.ac("S1-AC2")
def test_ac2_quantity_valid_boundary_99():
    """Quantity of 99 is valid"""
    catalog = {"SKU1": Product(sku="SKU1", name="Product 1", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU1", quantity=99)]
    quote = price_cart(lines, catalog, today=date(2026, 10, 3))
    assert quote.subtotal == Decimal("990.00")


# S1-AC3: SKU validation
@pytest.mark.ac("S1-AC3")
def test_ac3_sku_not_in_catalog():
    """A line with SKU not in catalog raises CartError"""
    catalog = {"SKU1": Product(sku="SKU1", name="Product 1", unit_price=Decimal("10.00"))}
    lines = [Line(sku="UNKNOWN", quantity=5)]
    with pytest.raises(CartError):
        price_cart(lines, catalog, today=date(2026, 10, 3))


@pytest.mark.ac("S1-AC3")
def test_ac3_missing_sku_with_valid_sku():
    """Error raised even when other SKUs are in catalog"""
    catalog = {
        "SKU1": Product(sku="SKU1", name="Product 1", unit_price=Decimal("10.00")),
        "SKU2": Product(sku="SKU2", name="Product 2", unit_price=Decimal("20.00")),
    }
    lines = [Line(sku="SKU1", quantity=1), Line(sku="UNKNOWN", quantity=5)]
    with pytest.raises(CartError):
        price_cart(lines, catalog, today=date(2026, 10, 3))


# S1-AC4: Line merging
@pytest.mark.ac("S1-AC4")
def test_ac4_duplicate_sku_lines_merged():
    """Lines with same SKU are merged, adding quantities"""
    catalog = {"SKU1": Product(sku="SKU1", name="Product 1", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU1", quantity=5), Line(sku="SKU1", quantity=3)]
    quote = price_cart(lines, catalog, today=date(2026, 10, 3))
    assert quote.subtotal == Decimal("80.00")


@pytest.mark.ac("S1-AC4")
def test_ac4_multiple_duplicate_lines():
    """Multiple lines with same SKU are all merged"""
    catalog = {"SKU1": Product(sku="SKU1", name="Product 1", unit_price=Decimal("10.00"))}
    lines = [
        Line(sku="SKU1", quantity=2),
        Line(sku="SKU1", quantity=3),
        Line(sku="SKU1", quantity=4),
    ]
    quote = price_cart(lines, catalog, today=date(2026, 10, 3))
    assert quote.subtotal == Decimal("90.00")


@pytest.mark.ac("S1-AC4")
def test_ac4_merged_quantity_exceeds_99():
    """Merged quantity exceeding 99 raises CartError"""
    catalog = {"SKU1": Product(sku="SKU1", name="Product 1", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU1", quantity=60), Line(sku="SKU1", quantity=40)]
    with pytest.raises(CartError):
        price_cart(lines, catalog, today=date(2026, 10, 3))


@pytest.mark.ac("S1-AC4")
def test_ac4_merged_quantity_exactly_99():
    """Merged quantity of exactly 99 is valid"""
    catalog = {"SKU1": Product(sku="SKU1", name="Product 1", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU1", quantity=50), Line(sku="SKU1", quantity=49)]
    quote = price_cart(lines, catalog, today=date(2026, 10, 3))
    assert quote.subtotal == Decimal("990.00")


# S1-AC5: Empty cart
@pytest.mark.ac("S1-AC5")
def test_ac5_empty_cart_all_zeros():
    """Empty cart has all amounts as 0.00"""
    catalog = {}
    lines = []
    quote = price_cart(lines, catalog, today=date(2026, 10, 3))
    assert quote.subtotal == Decimal("0.00")
    assert quote.discount == Decimal("0.00")
    assert quote.shipping == Decimal("0.00")
    assert quote.tax == Decimal("0.00")
    assert quote.total == Decimal("0.00")


@pytest.mark.ac("S1-AC5")
def test_ac5_empty_cart_nothing_applied():
    """Empty cart has nothing in applied"""
    catalog = {}
    lines = []
    quote = price_cart(lines, catalog, today=date(2026, 10, 3))
    assert quote.applied == ()


@pytest.mark.ac("S1-AC5")
def test_ac5_empty_cart_ignores_coupon():
    """Empty cart ignores coupon"""
    catalog = {}
    lines = []
    coupon = Coupon(code="SAVE10", kind="percent", value=Decimal("10"))
    quote = price_cart(lines, catalog, today=date(2026, 10, 3), coupon=coupon)
    assert quote.subtotal == Decimal("0.00")
    assert quote.discount == Decimal("0.00")
    assert quote.total == Decimal("0.00")


@pytest.mark.ac("S1-AC5")
def test_ac5_empty_cart_ignores_loyalty():
    """Empty cart ignores loyalty tier"""
    catalog = {}
    lines = []
    customer = Customer(tier="gold")
    quote = price_cart(lines, catalog, today=date(2026, 10, 3), customer=customer)
    assert quote.subtotal == Decimal("0.00")
    assert quote.discount == Decimal("0.00")
    assert quote.total == Decimal("0.00")


@pytest.mark.ac("S1-AC5")
def test_ac5_empty_cart_no_shipping():
    """Empty cart does not charge shipping"""
    catalog = {}
    lines = []
    quote = price_cart(lines, catalog, today=date(2026, 10, 3), shipping="standard")
    assert quote.shipping == Decimal("0.00")
    assert quote.total == Decimal("0.00")
```