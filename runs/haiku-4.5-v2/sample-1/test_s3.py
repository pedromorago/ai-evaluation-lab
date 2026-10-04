import pytest
from decimal import Decimal
from datetime import date
from checkout import price_cart, Product, Line, Coupon, CouponError


# S3-AC1: Percent coupon

@pytest.mark.ac("S3-AC1")
def test_percent_coupon_10_percent():
    """A percent coupon with value 10 applies 10% off the subtotal"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    coupon = Coupon(code="SAVE10", kind="percent", value=Decimal("10"))
    
    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        coupon=coupon
    )
    
    # Subtotal: 100.00
    # Coupon discount: 10% of 100.00 = 10.00
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("10.00")
    assert "coupon:SAVE10" in quote.applied


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_25_percent():
    """A percent coupon applies the specified percentage"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("200.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    coupon = Coupon(code="SAVE25", kind="percent", value=Decimal("25"))
    
    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        coupon=coupon
    )
    
    # Subtotal: 200.00
    # Coupon discount: 25% of 200.00 = 50.00
    assert quote.subtotal == Decimal("200.00")
    assert quote.discount == Decimal("50.00")
    assert "coupon:SAVE25" in quote.applied


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_fractional_discount():
    """A percent coupon correctly handles fractional discounts"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("150.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    coupon = Coupon(code="SAVE5", kind="percent", value=Decimal("5"))
    
    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        coupon=coupon
    )
    
    # Subtotal: 150.00
    # Coupon discount: 5% of 150.00 = 7.50
    assert quote.subtotal == Decimal("150.00")
    assert quote.discount == Decimal("7.50")
    assert "coupon:SAVE5" in quote.applied


# S3-AC2: Fixed coupon

@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_subtracts_euros():
    """A fixed coupon takes euros off the subtotal"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    coupon = Coupon(code="SAVEFIX", kind="fixed", value=Decimal("25.00"))
    
    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        coupon=coupon
    )
    
    # Subtotal: 100.00
    # Fixed discount: 25.00
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("25.00")
    assert "coupon:SAVEFIX" in quote.applied


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_never_goes_below_zero():
    """A fixed coupon never takes the goods below 0.00"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("10.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    coupon = Coupon(code="SAVEFIX", kind="fixed", value=Decimal("50.00"))
    
    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        coupon=coupon
    )
    
    # Subtotal: 10.00
    # Fixed discount requested: 50.00, but capped at 10.00
    assert quote.subtotal == Decimal("10.00")
    assert quote.discount == Decimal("10.00")
    assert "coupon:SAVEFIX" in quote.applied


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_partial_offset():
    """A fixed coupon takes the specified amount without going below zero"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("30.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    coupon = Coupon(code="SAVEFIX", kind="fixed", value=Decimal("15.00"))
    
    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        coupon=coupon
    )
    
    # Subtotal: 30.00
    # Fixed discount: 15.00 (no capping needed)
    assert quote.subtotal == Decimal("30.00")
    assert quote.discount == Decimal("15.00")
    assert "coupon:SAVEFIX" in quote.applied


# S3-AC3: Minimum subtotal

@pytest.mark.ac("S3-AC3")
def test_coupon_min_subtotal_not_met():
    """A coupon raises CouponError when subtotal is below minimum"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("10.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    coupon = Coupon(
        code="MINORDER",
        kind="percent",
        value=Decimal("10"),
        min_subtotal=Decimal("50.00")
    )
    
    with pytest.raises(CouponError):
        price_cart(
            lines=lines,
            catalog=catalog,
            today=date(2026, 10, 3),
            coupon=coupon
        )


@pytest.mark.ac("S3-AC3")
def test_coupon_min_subtotal_exactly_met():
    """A coupon is valid when subtotal equals the minimum"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("50.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    coupon = Coupon(
        code="MINORDER",
        kind="percent",
        value=Decimal("10"),
        min_subtotal=Decimal("50.00")
    )
    
    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        coupon=coupon
    )
    
    # Subtotal: 50.00 (equals minimum)
    assert quote.subtotal == Decimal("50.00")
    assert "coupon:MINORDER" in quote.applied


@pytest.mark.ac("S3-AC3")
def test_coupon_min_subtotal_exceeded():
    """A coupon is valid when subtotal exceeds the minimum"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("60.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    coupon = Coupon(
        code="MINORDER",
        kind="percent",
        value=Decimal("10"),
        min_subtotal=Decimal("50.00")
    )
    
    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        coupon=coupon
    )
    
    # Subtotal: 60.00 (exceeds minimum)
    assert quote.subtotal == Decimal("60.00")
    assert "coupon:MINORDER" in quote.applied


# S3-AC4: Expiry date

@pytest.mark.ac("S3-AC4")
def test_coupon_after_expiry_raises_error():
    """A coupon raises CouponError when used after expiry date"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    coupon = Coupon(
        code="EXPIRED",
        kind="percent",
        value=Decimal("10"),
        expires=date(2026, 10, 1)
    )
    
    with pytest.raises(CouponError):
        price_cart(
            lines=lines,
            catalog=catalog,
            today=date(2026, 10, 3),
            coupon=coupon
        )


@pytest.mark.ac("S3-AC4")
def test_coupon_on_expiry_date_is_valid():
    """A coupon is valid on its expiry date"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    coupon = Coupon(
        code="LASTDAY",
        kind="percent",
        value=Decimal("10"),
        expires=date(2026, 10, 3)
    )
    
    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        coupon=coupon
    )
    
    # Subtotal: 100.00
    assert quote.subtotal == Decimal("100.00")
    assert "coupon:LASTDAY" in quote.applied


@pytest.mark.ac("S3-AC4")
def test_coupon_before_expiry_is_valid():
    """A coupon is valid before its expiry date"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    coupon = Coupon(
        code="VALIDYET",
        kind="percent",
        value=Decimal("10"),
        expires=date(2026, 10, 5)
    )
    
    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2026, 10, 3),
        coupon=coupon
    )
    
    # Subtotal: 100.00
    assert quote.subtotal == Decimal("100.00")
    assert "coupon:VALIDYET" in quote.applied


@pytest.mark.ac("S3-AC4")
def test_coupon_without_expiry_never_expires():
    """A coupon without expiry date never expires"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    coupon = Coupon(
        code="NEVEREXP",
        kind="percent",
        value=Decimal("10")
    )
    
    quote = price_cart(
        lines=lines,
        catalog=catalog,
        today=date(2099, 12, 31),
        coupon=coupon
    )
    
    # Subtotal: 100.00
    assert quote.subtotal == Decimal("100.00")
    assert "coupon:NEVEREXP" in quote.applied


# S3-AC5: Invalid kind

@pytest.mark.ac("S3-AC5")
def test_invalid_coupon_kind_raises_error():
    """A coupon with invalid kind raises CouponError"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    coupon = Coupon(
        code="INVALID",
        kind="discount",
        value=Decimal("10")
    )
    
    with pytest.raises(CouponError):
        price_cart(
            lines=lines,
            catalog=catalog,
            today=date(2026, 10, 3),
            coupon=coupon
        )


@pytest.mark.ac("S3-AC5")
def test_another_invalid_coupon_kind():
    """Another invalid coupon kind raises CouponError"""
    catalog = {
        "ITEM": Product(sku="ITEM", name="Item", unit_price=Decimal("100.00"))
    }
    lines = [Line(sku="ITEM", quantity=1)]
    coupon = Coupon(
        code="BOGO",
        kind="buy_one_get_one",
        value=Decimal("1")
    )
    
    with pytest.raises(CouponError):
        price_cart(
            lines=lines,
            catalog=catalog,
            today=date(2026, 10, 3),
            coupon=coupon
        )
