import pytest
from decimal import Decimal
from datetime import date
from checkout import price_cart, Product, Line, Customer, Coupon


@pytest.mark.ac("S4-AC1")
def test_gold_tier_gets_5_percent_loyalty_discount():
    """Gold tier customers receive 5% loyalty discount on subtotal."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("100.00"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=1)]
    customer = Customer(tier="gold")

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer
    )

    # Subtotal: 100.00 * 1 = 100.00
    # Loyalty discount (5% of 100.00): 5.00
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("5.00")
    assert "loyalty" in quote.applied


@pytest.mark.ac("S4-AC1")
def test_standard_tier_gets_no_loyalty_discount():
    """Standard tier customers get no loyalty discount."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("100.00"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=1)]
    customer = Customer(tier="standard")

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer
    )

    # Subtotal: 100.00
    # Loyalty discount (0% for standard): 0.00
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("0.00")
    assert "loyalty" not in quote.applied


@pytest.mark.ac("S4-AC2")
def test_loyalty_5_percent_wins_over_percent_coupon_3_percent():
    """When loyalty (5%) is larger than percent coupon, loyalty wins."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("100.00"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="SAVE3", kind="percent", value=Decimal("3"))

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer,
        coupon=coupon
    )

    # Subtotal: 100.00
    # Loyalty: 100.00 * 5% = 5.00
    # Coupon: 100.00 * 3% = 3.00
    # Apply loyalty (5.00 > 3.00)
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("5.00")
    assert quote.applied == ("loyalty",)


@pytest.mark.ac("S4-AC2")
def test_percent_coupon_8_percent_wins_over_loyalty_5_percent():
    """When percent coupon is larger than loyalty, coupon wins."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("100.00"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="SAVE8", kind="percent", value=Decimal("8"))

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer,
        coupon=coupon
    )

    # Subtotal: 100.00
    # Loyalty: 100.00 * 5% = 5.00
    # Coupon: 100.00 * 8% = 8.00
    # Apply coupon (8.00 > 5.00)
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("8.00")
    assert quote.applied == ("coupon:SAVE8",)


@pytest.mark.ac("S4-AC2")
def test_percent_coupon_wins_when_equal_to_loyalty():
    """When percent coupon equals loyalty (5%), coupon wins."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("100.00"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="SAVE5", kind="percent", value=Decimal("5"))

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer,
        coupon=coupon
    )

    # Subtotal: 100.00
    # Loyalty: 100.00 * 5% = 5.00
    # Coupon: 100.00 * 5% = 5.00
    # Apply coupon (equal means coupon wins)
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("5.00")
    assert quote.applied == ("coupon:SAVE5",)


@pytest.mark.ac("S4-AC2")
def test_fixed_coupon_stacks_with_loyalty_discount():
    """Fixed coupon stacks with loyalty discount, applied after."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("100.00"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="FIXED10", kind="fixed", value=Decimal("10"))

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer,
        coupon=coupon
    )

    # Subtotal: 100.00
    # Loyalty discount (5%): 100.00 * 0.05 = 5.00
    # After loyalty: 100.00 - 5.00 = 95.00
    # Fixed coupon: 10.00
    # Total discount: 5.00 + 10.00 = 15.00
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("15.00")
    assert quote.applied == ("loyalty", "coupon:FIXED10")


@pytest.mark.ac("S4-AC1")
def test_standard_tier_receives_no_loyalty_with_fixed_coupon():
    """Standard tier gets no loyalty; only fixed coupon applies."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("100.00"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=1)]
    customer = Customer(tier="standard")
    coupon = Coupon(code="FIXED10", kind="fixed", value=Decimal("10"))

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer,
        coupon=coupon
    )

    # Subtotal: 100.00
    # Loyalty discount (0% for standard): 0.00
    # Fixed coupon: 10.00
    # Total discount: 10.00
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("10.00")
    assert quote.applied == ("coupon:FIXED10",)


@pytest.mark.ac("S4-AC1", "S4-AC2")
def test_loyalty_applies_after_volume_discount():
    """Loyalty applies to subtotal after volume discount."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("10.00"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=10)]
    customer = Customer(tier="gold")

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer
    )

    # Line cost: 10.00 * 10 = 100.00
    # Volume discount (10+): 100.00 * 10% = 10.00
    # Subtotal after volume: 100.00 - 10.00 = 90.00
    # Loyalty (5% of 90.00): 4.50
    # Total discount: 10.00 + 4.50 = 14.50
    assert quote.subtotal == Decimal("90.00")
    assert quote.discount == Decimal("14.50")
    assert quote.applied == ("volume:PROD-1", "loyalty")


@pytest.mark.ac("S4-AC1")
def test_loyalty_discount_rounded_half_up():
    """Loyalty discount is rounded half up to the cent."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("33.33"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=1)]
    customer = Customer(tier="gold")

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer
    )

    # Subtotal: 33.33
    # Loyalty (5%): 33.33 * 0.05 = 1.6665 -> rounds half up to 1.67
    assert quote.subtotal == Decimal("33.33")
    assert quote.discount == Decimal("1.67")


@pytest.mark.ac("S4-AC2")
def test_loyalty_5_percent_wins_over_coupon_1_percent():
    """Loyalty 5% beats percent coupon 1%."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("100.00"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="SAVE1", kind="percent", value=Decimal("1"))

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer,
        coupon=coupon
    )

    # Subtotal: 100.00
    # Loyalty: 100.00 * 5% = 5.00
    # Coupon: 100.00 * 1% = 1.00
    # Apply loyalty (5.00 > 1.00)
    assert quote.discount == Decimal("5.00")
    assert quote.applied == ("loyalty",)


@pytest.mark.ac("S4-AC2")
def test_fixed_coupon_capped_by_remaining_balance():
    """Fixed coupon never takes goods below 0.00."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("20.00"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="FIXED50", kind="fixed", value=Decimal("50"))

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer,
        coupon=coupon
    )

    # Subtotal: 20.00
    # Loyalty (5%): 20.00 * 0.05 = 1.00
    # After loyalty: 20.00 - 1.00 = 19.00
    # Fixed coupon: min(50.00, 19.00) = 19.00
    # Total discount: 1.00 + 19.00 = 20.00
    assert quote.subtotal == Decimal("20.00")
    assert quote.discount == Decimal("20.00")


@pytest.mark.ac("S4-AC2")
def test_applied_shows_loyalty_before_fixed_coupon():
    """Applied tuple shows loyalty before fixed coupon."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("100.00"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="FIXED5", kind="fixed", value=Decimal("5"))

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer,
        coupon=coupon
    )

    # Applied should show loyalty before fixed coupon
    assert quote.applied == ("loyalty", "coupon:FIXED5")


@pytest.mark.ac("S4-AC1")
def test_loyalty_discount_on_multiple_items():
    """Loyalty applies to total subtotal of multiple items."""
    product1 = Product(sku="PROD-1", name="Widget", unit_price=Decimal("50.00"))
    product2 = Product(sku="PROD-2", name="Gadget", unit_price=Decimal("30.00"))
    catalog = {"PROD-1": product1, "PROD-2": product2}
    lines = [
        Line(sku="PROD-1", quantity=1),
        Line(sku="PROD-2", quantity=1)
    ]
    customer = Customer(tier="gold")

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer
    )

    # Subtotal: 50.00 + 30.00 = 80.00
    # Loyalty (5%): 80.00 * 0.05 = 4.00
    assert quote.subtotal == Decimal("80.00")
    assert quote.discount == Decimal("4.00")
    assert "loyalty" in quote.applied


@pytest.mark.ac("S4-AC2")
def test_loyalty_5_percent_wins_over_coupon_4_percent():
    """Loyalty 5% beats percent coupon 4%."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("100.00"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="SAVE4", kind="percent", value=Decimal("4"))

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer,
        coupon=coupon
    )

    # Subtotal: 100.00
    # Loyalty: 100.00 * 5% = 5.00
    # Coupon: 100.00 * 4% = 4.00
    # Apply loyalty (5.00 > 4.00)
    assert quote.discount == Decimal("5.00")
    assert quote.applied == ("loyalty",)


@pytest.mark.ac("S4-AC2")
def test_coupon_6_percent_wins_over_loyalty_5_percent():
    """Percent coupon 6% beats loyalty 5%."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("100.00"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="SAVE6", kind="percent", value=Decimal("6"))

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer,
        coupon=coupon
    )

    # Subtotal: 100.00
    # Loyalty: 100.00 * 5% = 5.00
    # Coupon: 100.00 * 6% = 6.00
    # Apply coupon (6.00 > 5.00)
    assert quote.discount == Decimal("6.00")
    assert quote.applied == ("coupon:SAVE6",)


@pytest.mark.ac("S4-AC2")
def test_fixed_coupon_with_multiple_items_and_loyalty():
    """Fixed coupon stacks with loyalty on subtotal of multiple items."""
    product1 = Product(sku="PROD-1", name="Widget", unit_price=Decimal("60.00"))
    product2 = Product(sku="PROD-2", name="Gadget", unit_price=Decimal("40.00"))
    catalog = {"PROD-1": product1, "PROD-2": product2}
    lines = [
        Line(sku="PROD-1", quantity=1),
        Line(sku="PROD-2", quantity=1)
    ]
    customer = Customer(tier="gold")
    coupon = Coupon(code="FIXED20", kind="fixed", value=Decimal("20"))

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer,
        coupon=coupon
    )

    # Subtotal: 60.00 + 40.00 = 100.00
    # Loyalty (5%): 100.00 * 0.05 = 5.00
    # After loyalty: 100.00 - 5.00 = 95.00
    # Fixed coupon: 20.00
    # Total discount: 5.00 + 20.00 = 25.00
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("25.00")
    assert quote.applied == ("loyalty", "coupon:FIXED20")


@pytest.mark.ac("S4-AC1")
def test_loyalty_with_larger_subtotal_rounding():
    """Loyalty discount with larger amount rounds correctly."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("66.67"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=1)]
    customer = Customer(tier="gold")

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer
    )

    # Subtotal: 66.67
    # Loyalty (5%): 66.67 * 0.05 = 3.3335 -> rounds to 3.33
    assert quote.subtotal == Decimal("66.67")
    assert quote.discount == Decimal("3.33")


@pytest.mark.ac("S4-AC2")
def test_loyalty_vs_coupon_comparison_on_different_subtotal():
    """Loyalty and coupon percentages are compared as absolute discounts."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("200.00"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="SAVE6", kind="percent", value=Decimal("6"))

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer,
        coupon=coupon
    )

    # Subtotal: 200.00
    # Loyalty (5%): 200.00 * 0.05 = 10.00
    # Coupon (6%): 200.00 * 0.06 = 12.00
    # Apply coupon (12.00 > 10.00)
    assert quote.subtotal == Decimal("200.00")
    assert quote.discount == Decimal("12.00")
    assert quote.applied == ("coupon:SAVE6",)


@pytest.mark.ac("S4-AC2")
def test_fixed_coupon_exactly_equals_remaining_balance():
    """Fixed coupon applying exactly the remaining balance."""
    product = Product(sku="PROD-1", name="Widget", unit_price=Decimal("100.00"))
    catalog = {"PROD-1": product}
    lines = [Line(sku="PROD-1", quantity=1)]
    customer = Customer(tier="gold")
    coupon = Coupon(code="FIXED95", kind="fixed", value=Decimal("95"))

    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        customer=customer,
        coupon=coupon
    )

    # Subtotal: 100.00
    # Loyalty (5%): 5.00
    # After loyalty: 95.00
    # Fixed coupon: 95.00 (exactly equals remaining)
    # Total discount: 5.00 + 95.00 = 100.00
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("100.00")
