```python
import pytest
from datetime import date
from decimal import Decimal
from checkout import price_cart, Product, Line, Customer, Coupon, CartError

TODAY = date(2025, 1, 1)


# S5-AC1: Standard shipping costs 4.99, free when goods >= 50.00 after discounts

@pytest.mark.ac("S5-AC1")
def test_standard_shipping_costs_4_99():
    """Standard shipping costs 4.99 on orders below 50.00."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=2)]
    quote = price_cart(lines, catalog, today=TODAY, shipping="standard")
    assert quote.shipping == Decimal("4.99")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_at_50():
    """Standard shipping is free when goods total exactly 50.00 after discounts."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("25.00"))}
    lines = [Line(sku="SKU-1", quantity=2)]
    quote = price_cart(lines, catalog, today=TODAY, shipping="standard")
    assert quote.subtotal == Decimal("50.00")
    assert quote.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_above_50():
    """Standard shipping is free when goods total more than 50.00 after discounts."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("30.00"))}
    lines = [Line(sku="SKU-1", quantity=2)]
    quote = price_cart(lines, catalog, today=TODAY, shipping="standard")
    assert quote.subtotal == Decimal("60.00")
    assert quote.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_after_volume_discount():
    """Standard shipping free threshold applies after volume discount."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=50)]  # 500 before, 425 after 15% discount
    quote = price_cart(lines, catalog, today=TODAY, shipping="standard")
    assert quote.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_after_loyalty_discount():
    """Standard shipping free threshold applies after loyalty discount."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("60.00"))}
    lines = [Line(sku="SKU-1", quantity=1)]
    customer = Customer(tier="gold")
    quote = price_cart(lines, catalog, today=TODAY, customer=customer, shipping="standard")
    # Subtotal 60.00, after 5% loyalty discount = 57.00, above 50
    assert quote.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_after_percent_coupon():
    """Standard shipping free threshold applies after percent coupon."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("100.00"))}
    lines = [Line(sku="SKU-1", quantity=1)]
    coupon = Coupon(code="SAVE40", kind="percent", value=Decimal("40"))
    quote = price_cart(lines, catalog, today=TODAY, coupon=coupon, shipping="standard")
    # Subtotal 100.00, after 40% coupon = 60.00, above 50
    assert quote.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_after_fixed_coupon():
    """Standard shipping free threshold applies after fixed coupon."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("100.00"))}
    lines = [Line(sku="SKU-1", quantity=1)]
    coupon = Coupon(code="SAVE50", kind="fixed", value=Decimal("50.00"))
    quote = price_cart(lines, catalog, today=TODAY, coupon=coupon, shipping="standard")
    # Subtotal 100.00, after 50.00 fixed coupon = 50.00, at threshold
    assert quote.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_charged_below_50():
    """Standard shipping charged when goods total below 50.00 after discounts."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("45.00"))}
    lines = [Line(sku="SKU-1", quantity=1)]
    quote = price_cart(lines, catalog, today=TODAY, shipping="standard")
    assert quote.subtotal == Decimal("45.00")
    assert quote.shipping == Decimal("4.99")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_on_empty_cart():
    """Standard shipping is free on empty cart (no goods to ship)."""
    catalog = {}
    lines = []
    quote = price_cart(lines, catalog, today=TODAY, shipping="standard")
    assert quote.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_free_with_multiple_items():
    """Standard shipping free threshold works with multiple items."""
    catalog = {
        "SKU-1": Product(sku="SKU-1", name="Item 1", unit_price=Decimal("25.00")),
        "SKU-2": Product(sku="SKU-2", name="Item 2", unit_price=Decimal("25.00")),
    }
    lines = [Line(sku="SKU-1", quantity=1), Line(sku="SKU-2", quantity=1)]
    quote = price_cart(lines, catalog, today=TODAY, shipping="standard")
    assert quote.subtotal == Decimal("50.00")
    assert quote.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_with_books_no_volume_discount():
    """Standard shipping threshold includes books (which don't get volume discount)."""
    catalog = {"BOOK-1": Product(sku="BOOK-1", name="Book", unit_price=Decimal("10.00"), category="books")}
    lines = [Line(sku="BOOK-1", quantity=5)]  # 5 units * 10 = 50, no volume discount
    quote = price_cart(lines, catalog, today=TODAY, shipping="standard")
    assert quote.subtotal == Decimal("50.00")
    assert quote.shipping == Decimal("0.00")


# S5-AC2: Express shipping costs 9.99 and is never free

@pytest.mark.ac("S5-AC2")
def test_express_shipping_costs_9_99():
    """Express shipping costs 9.99 on small orders."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=1)]
    quote = price_cart(lines, catalog, today=TODAY, shipping="express")
    assert quote.shipping == Decimal("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_on_large_order():
    """Express shipping costs 9.99 even on large orders (never free)."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("100.00"))}
    lines = [Line(sku="SKU-1", quantity=10)]
    quote = price_cart(lines, catalog, today=TODAY, shipping="express")
    assert quote.subtotal == Decimal("1000.00")
    assert quote.shipping == Decimal("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_never_free_with_all_discounts():
    """Express shipping costs 9.99 even with all discounts applied."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("100.00"))}
    lines = [Line(sku="SKU-1", quantity=50)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="SAVE10", kind="percent", value=Decimal("10"))
    quote = price_cart(lines, catalog, today=TODAY, customer=customer, coupon=coupon, shipping="express")
    assert quote.shipping == Decimal("9.99")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_on_empty_cart():
    """Express shipping is free on empty cart (no goods to ship)."""
    catalog = {}
    lines = []
    quote = price_cart(lines, catalog, today=TODAY, shipping="express")
    assert quote.shipping == Decimal("0.00")


@pytest.mark.ac("S5-AC2")
def test_express_shipping_on_order_just_under_50():
    """Express shipping costs 9.99 even on orders just under 50.00."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("49.99"))}
    lines = [Line(sku="SKU-1", quantity=1)]
    quote = price_cart(lines, catalog, today=TODAY, shipping="express")
    assert quote.subtotal == Decimal("49.99")
    assert quote.shipping == Decimal("9.99")


# S5-AC3: Any other shipping method raises CartError

@pytest.mark.ac("S5-AC3")
def test_invalid_shipping_overnight():
    """Invalid shipping method raises CartError."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=1)]
    with pytest.raises(CartError):
        price_cart(lines, catalog, today=TODAY, shipping="overnight")


@pytest.mark.ac("S5-AC3")
def test_invalid_shipping_empty():
    """Empty shipping method raises CartError."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=1)]
    with pytest.raises(CartError):
        price_cart(lines, catalog, today=TODAY, shipping="")


@pytest.mark.ac("S5-AC3")
def test_invalid_shipping_typo():
    """Typo in shipping method raises CartError."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=1)]
    with pytest.raises(CartError):
        price_cart(lines, catalog, today=TODAY, shipping="standrd")


@pytest.mark.ac("S5-AC3")
def test_invalid_shipping_premium():
    """Premium shipping method raises CartError."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=1)]
    with pytest.raises(CartError):
        price_cart(lines, catalog, today=TODAY, shipping="premium")


@pytest.mark.ac("S5-AC3")
def test_invalid_shipping_same_day():
    """Same-day shipping method raises CartError."""
    catalog = {"SKU-1": Product(sku="SKU-1", name="Item", unit_price=Decimal("10.00"))}
    lines = [Line(sku="SKU-1", quantity=1)]
    with pytest.raises(CartError):
        price_cart(lines, catalog, today=TODAY, shipping="same-day")
```