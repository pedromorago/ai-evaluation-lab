import pytest
from decimal import Decimal
from datetime import date
from checkout import (
    price_cart, Product, Line, Coupon, CouponError
)


@pytest.fixture
def catalog():
    return {
        "ITEM-1": Product(sku="ITEM-1", name="Item 1", unit_price=Decimal("10.00")),
    }


@pytest.fixture
def today():
    return date(2026, 1, 1)


# S3-AC1: Percent coupon tests
@pytest.mark.ac("S3-AC1")
def test_percent_coupon_10_percent_off(catalog, today):
    """10% coupon on $10 item = $1 discount"""
    lines = [Line(sku="ITEM-1", quantity=1)]
    coupon = Coupon(code="SAVE10", kind="percent", value=Decimal("10"))
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    assert quote.subtotal == Decimal("10.00")
    assert quote.discount == Decimal("1.00")
    assert "coupon:SAVE10" in quote.applied


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_50_percent_off(catalog, today):
    """50% coupon on $10 item = $5 discount"""
    lines = [Line(sku="ITEM-1", quantity=1)]
    coupon = Coupon(code="SAVE50", kind="percent", value=Decimal("50"))
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    assert quote.subtotal == Decimal("10.00")
    assert quote.discount == Decimal("5.00")


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_on_larger_subtotal(catalog, today):
    """20% coupon on $100 subtotal = $20 discount"""
    lines = [Line(sku="ITEM-1", quantity=10)]
    coupon = Coupon(code="SAVE20", kind="percent", value=Decimal("20"))
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("20.00")


# S3-AC2: Fixed coupon tests
@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_5_euros_off(catalog, today):
    """$5 fixed coupon on $10 item = $5 discount"""
    lines = [Line(sku="ITEM-1", quantity=1)]
    coupon = Coupon(code="SAVE5", kind="fixed", value=Decimal("5.00"))
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    assert quote.subtotal == Decimal("10.00")
    assert quote.discount == Decimal("5.00")


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_exceeding_subtotal_capped_at_zero(catalog, today):
    """$100 fixed coupon on $10 item should not reduce total below 0"""
    lines = [Line(sku="ITEM-1", quantity=1)]
    coupon = Coupon(code="SAVE100", kind="fixed", value=Decimal("100.00"))
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    assert quote.subtotal == Decimal("10.00")
    # Discount should not exceed subtotal
    assert quote.discount <= quote.subtotal


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_on_larger_subtotal(catalog, today):
    """$10 fixed coupon on $100 subtotal = $10 discount"""
    lines = [Line(sku="ITEM-1", quantity=10)]
    coupon = Coupon(code="SAVE10", kind="fixed", value=Decimal("10.00"))
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("10.00")


# S3-AC3: Minimum subtotal tests
@pytest.mark.ac("S3-AC3")
def test_coupon_applies_when_subtotal_equals_minimum(catalog, today):
    """Coupon should apply when subtotal equals min_subtotal"""
    lines = [Line(sku="ITEM-1", quantity=1)]
    coupon = Coupon(
        code="SAVE10", kind="percent", value=Decimal("10"),
        min_subtotal=Decimal("10.00")
    )
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    assert quote.subtotal == Decimal("10.00")
    assert quote.discount == Decimal("1.00")


@pytest.mark.ac("S3-AC3")
def test_coupon_raises_error_when_subtotal_below_minimum(catalog, today):
    """Coupon should raise CouponError when subtotal is below min_subtotal"""
    lines = [Line(sku="ITEM-1", quantity=1)]
    coupon = Coupon(
        code="SAVE10", kind="percent", value=Decimal("10"),
        min_subtotal=Decimal("20.00")
    )
    with pytest.raises(CouponError):
        price_cart(lines, catalog, today=today, coupon=coupon)


@pytest.mark.ac("S3-AC3")
def test_coupon_applies_when_subtotal_above_minimum(catalog, today):
    """Coupon should apply when subtotal is above min_subtotal"""
    lines = [Line(sku="ITEM-1", quantity=2)]
    coupon = Coupon(
        code="SAVE10", kind="percent", value=Decimal("10"),
        min_subtotal=Decimal("10.00")
    )
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    assert quote.subtotal == Decimal("20.00")
    assert quote.discount == Decimal("2.00")


# S3-AC4: Expiry date tests
@pytest.mark.ac("S3-AC4")
def test_coupon_valid_on_expiry_date(catalog):
    """Coupon should be valid on its expiry date"""
    lines = [Line(sku="ITEM-1", quantity=1)]
    expiry = date(2026, 1, 1)
    coupon = Coupon(code="SAVE10", kind="percent", value=Decimal("10"), expires=expiry)
    quote = price_cart(lines, catalog, today=expiry, coupon=coupon)
    assert quote.discount == Decimal("1.00")
    assert "coupon:SAVE10" in quote.applied


@pytest.mark.ac("S3-AC4")
def test_coupon_invalid_after_expiry_date(catalog):
    """Coupon should raise CouponError after its expiry date"""
    lines = [Line(sku="ITEM-1", quantity=1)]
    expiry = date(2026, 1, 1)
    next_day = date(2026, 1, 2)
    coupon = Coupon(code="SAVE10", kind="percent", value=Decimal("10"), expires=expiry)
    with pytest.raises(CouponError):
        price_cart(lines, catalog, today=next_day, coupon=coupon)


@pytest.mark.ac("S3-AC4")
def test_coupon_valid_before_expiry_date(catalog):
    """Coupon should be valid before its expiry date"""
    lines = [Line(sku="ITEM-1", quantity=1)]
    expiry = date(2026, 1, 31)
    today = date(2026, 1, 1)
    coupon = Coupon(code="SAVE10", kind="percent", value=Decimal("10"), expires=expiry)
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    assert quote.discount == Decimal("1.00")


@pytest.mark.ac("S3-AC4")
def test_coupon_without_expiry_never_expires(catalog):
    """Coupon without expiry date should never expire"""
    lines = [Line(sku="ITEM-1", quantity=1)]
    coupon = Coupon(code="SAVE10", kind="percent", value=Decimal("10"), expires=None)
    far_future = date(2100, 1, 1)
    quote = price_cart(lines, catalog, today=far_future, coupon=coupon)
    assert quote.discount == Decimal("1.00")


# S3-AC5: Invalid coupon kind tests
@pytest.mark.ac("S3-AC5")
def test_coupon_invalid_kind_raises_error(catalog, today):
    """Coupon with kind neither 'percent' nor 'fixed' raises CouponError"""
    lines = [Line(sku="ITEM-1", quantity=1)]
    coupon = Coupon(code="BAD", kind="invalid", value=Decimal("10"))
    with pytest.raises(CouponError):
        price_cart(lines, catalog, today=today, coupon=coupon)


@pytest.mark.ac("S3-AC5")
def test_coupon_kind_discount_raises_error(catalog, today):
    """Coupon with kind 'discount' raises CouponError"""
    lines = [Line(sku="ITEM-1", quantity=1)]
    coupon = Coupon(code="BAD", kind="discount", value=Decimal("10"))
    with pytest.raises(CouponError):
        price_cart(lines, catalog, today=today, coupon=coupon)


@pytest.mark.ac("S3-AC5")
def test_coupon_kind_empty_string_raises_error(catalog, today):
    """Coupon with empty kind raises CouponError"""
    lines = [Line(sku="ITEM-1", quantity=1)]
    coupon = Coupon(code="BAD", kind="", value=Decimal("10"))
    with pytest.raises(CouponError):
        price_cart(lines, catalog, today=today, coupon=coupon)
