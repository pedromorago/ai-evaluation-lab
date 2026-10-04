import pytest
from datetime import date
from decimal import Decimal
from checkout import (
    CartError, CouponError, Product, Line, Customer, Coupon, 
    price_cart
)


# S3-AC1: Percent coupon discount
@pytest.mark.ac("S3-AC1")
def test_percent_coupon_10_percent_off():
    """A percent coupon with value 10 means 10% off the subtotal."""
    catalog = {"SKU-A": Product("SKU-A", "Item A", Decimal("100.00"))}
    lines = [Line("SKU-A", 1)]
    coupon = Coupon("SAVE10", "percent", Decimal("10"))
    today = date(2026, 1, 1)
    
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    
    # Subtotal: 100.00 * 1 = 100.00
    # Coupon discount: 10% of 100.00 = 10.00
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("10.00")
    assert "coupon:SAVE10" in quote.applied


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_50_percent_off():
    """A percent coupon with value 50 means 50% off."""
    catalog = {"SKU-B": Product("SKU-B", "Item B", Decimal("100.00"))}
    lines = [Line("SKU-B", 1)]
    coupon = Coupon("HALF", "percent", Decimal("50"))
    today = date(2026, 1, 1)
    
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    
    # Subtotal: 100.00
    # Coupon discount: 50% of 100.00 = 50.00
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("50.00")


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_decimal_amount_with_rounding():
    """A percent coupon works with decimal amounts and rounds half up."""
    catalog = {"SKU-C": Product("SKU-C", "Item C", Decimal("33.33"))}
    lines = [Line("SKU-C", 1)]
    coupon = Coupon("SAVE15", "percent", Decimal("15"))
    today = date(2026, 1, 1)
    
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    
    # Subtotal: 33.33
    # Coupon discount: 15% of 33.33 = 4.9995, rounded half up to cent = 5.00
    assert quote.subtotal == Decimal("33.33")
    assert quote.discount == Decimal("5.00")


# S3-AC2: Fixed coupon discount
@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_euros_off():
    """A fixed coupon takes its value in euros off the goods."""
    catalog = {"SKU-D": Product("SKU-D", "Item D", Decimal("100.00"))}
    lines = [Line("SKU-D", 1)]
    coupon = Coupon("MINUS10", "fixed", Decimal("10.00"))
    today = date(2026, 1, 1)
    
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    
    # Subtotal: 100.00
    # Coupon discount: 10.00
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("10.00")


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_never_below_zero():
    """A fixed coupon never takes the goods below 0.00."""
    catalog = {"SKU-E": Product("SKU-E", "Item E", Decimal("5.00"))}
    lines = [Line("SKU-E", 1)]
    coupon = Coupon("BIG", "fixed", Decimal("20.00"))
    today = date(2026, 1, 1)
    
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    
    # Subtotal: 5.00
    # Coupon discount would be 20.00, but clamped to 5.00
    assert quote.subtotal == Decimal("5.00")
    assert quote.discount == Decimal("5.00")


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_exact_subtotal():
    """A fixed coupon can equal the subtotal."""
    catalog = {"SKU-F": Product("SKU-F", "Item F", Decimal("10.00"))}
    lines = [Line("SKU-F", 1)]
    coupon = Coupon("EXACT", "fixed", Decimal("10.00"))
    today = date(2026, 1, 1)
    
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    
    # Subtotal: 10.00
    # Coupon discount: 10.00
    assert quote.subtotal == Decimal("10.00")
    assert quote.discount == Decimal("10.00")


# S3-AC3: Minimum subtotal requirement
@pytest.mark.ac("S3-AC3")
def test_coupon_subtotal_below_minimum_raises_error():
    """A coupon with min_subtotal raises CouponError when subtotal is below it."""
    catalog = {"SKU-G": Product("SKU-G", "Item G", Decimal("30.00"))}
    lines = [Line("SKU-G", 1)]
    coupon = Coupon("MIN100", "percent", Decimal("10"), min_subtotal=Decimal("100.00"))
    today = date(2026, 1, 1)
    
    # Subtotal: 30.00 < 100.00 minimum
    with pytest.raises(CouponError):
        price_cart(lines, catalog, today=today, coupon=coupon)


@pytest.mark.ac("S3-AC3")
def test_coupon_subtotal_equal_to_minimum_applies():
    """A subtotal equal to min_subtotal is enough for the coupon."""
    catalog = {"SKU-H": Product("SKU-H", "Item H", Decimal("50.00"))}
    lines = [Line("SKU-H", 2)]
    coupon = Coupon("MIN100", "percent", Decimal("10"), min_subtotal=Decimal("100.00"))
    today = date(2026, 1, 1)
    
    # Subtotal: 50.00 * 2 = 100.00 = minimum
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    
    assert quote.subtotal == Decimal("100.00")
    assert quote.discount == Decimal("10.00")


@pytest.mark.ac("S3-AC3")
def test_coupon_subtotal_above_minimum_applies():
    """A subtotal above min_subtotal applies the coupon."""
    catalog = {"SKU-I": Product("SKU-I", "Item I", Decimal("60.00"))}
    lines = [Line("SKU-I", 2)]
    coupon = Coupon("MIN100", "percent", Decimal("10"), min_subtotal=Decimal("100.00"))
    today = date(2026, 1, 1)
    
    # Subtotal: 60.00 * 2 = 120.00 > 100.00 minimum
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    
    assert quote.subtotal == Decimal("120.00")
    assert quote.discount == Decimal("12.00")


@pytest.mark.ac("S3-AC3")
def test_coupon_one_cent_below_minimum_raises_error():
    """A subtotal one cent below minimum raises CouponError."""
    catalog = {"SKU-J": Product("SKU-J", "Item J", Decimal("99.99"))}
    lines = [Line("SKU-J", 1)]
    coupon = Coupon("MIN100", "percent", Decimal("10"), min_subtotal=Decimal("100.00"))
    today = date(2026, 1, 1)
    
    # Subtotal: 99.99 < 100.00 minimum
    with pytest.raises(CouponError):
        price_cart(lines, catalog, today=today, coupon=coupon)


# S3-AC4: Expiry date validation
@pytest.mark.ac("S3-AC4")
def test_coupon_expired_raises_error():
    """A coupon raises CouponError after its expiry date."""
    catalog = {"SKU-K": Product("SKU-K", "Item K", Decimal("100.00"))}
    lines = [Line("SKU-K", 1)]
    coupon = Coupon("OLD", "percent", Decimal("10"), expires=date(2025, 12, 31))
    today = date(2026, 1, 1)
    
    # Today is after expiry date 2025-12-31
    with pytest.raises(CouponError):
        price_cart(lines, catalog, today=today, coupon=coupon)


@pytest.mark.ac("S3-AC4")
def test_coupon_on_expiry_date_applies():
    """A coupon is still valid on its expiry date."""
    catalog = {"SKU-L": Product("SKU-L", "Item L", Decimal("100.00"))}
    lines = [Line("SKU-L", 1)]
    coupon = Coupon("VALID", "percent", Decimal("10"), expires=date(2026, 1, 1))
    today = date(2026, 1, 1)
    
    # Today is on the expiry date
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    
    assert quote.discount == Decimal("10.00")
    assert "coupon:VALID" in quote.applied


@pytest.mark.ac("S3-AC4")
def test_coupon_before_expiry_date_applies():
    """A coupon is valid before its expiry date."""
    catalog = {"SKU-M": Product("SKU-M", "Item M", Decimal("100.00"))}
    lines = [Line("SKU-M", 1)]
    coupon = Coupon("FUTURE", "percent", Decimal("10"), expires=date(2026, 12, 31))
    today = date(2026, 1, 1)
    
    # Today is before expiry date 2026-12-31
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    
    assert quote.discount == Decimal("10.00")


@pytest.mark.ac("S3-AC4")
def test_coupon_without_expiry_never_expires():
    """A coupon without an expiry date never expires."""
    catalog = {"SKU-N": Product("SKU-N", "Item N", Decimal("100.00"))}
    lines = [Line("SKU-N", 1)]
    coupon = Coupon("ETERNAL", "percent", Decimal("10"), expires=None)
    today = date(2099, 12, 31)
    
    # Far in the future, but coupon has no expiry
    quote = price_cart(lines, catalog, today=today, coupon=coupon)
    
    assert quote.discount == Decimal("10.00")


@pytest.mark.ac("S3-AC4")
def test_coupon_one_day_after_expiry_raises_error():
    """A coupon raises CouponError one day after its expiry date."""
    catalog = {"SKU-O": Product("SKU-O", "Item O", Decimal("100.00"))}
    lines = [Line("SKU-O", 1)]
    coupon = Coupon("OLD", "percent", Decimal("10"), expires=date(2026, 1, 1))
    today = date(2026, 1, 2)
    
    # One day after expiry date
    with pytest.raises(CouponError):
        price_cart(lines, catalog, today=today, coupon=coupon)


# S3-AC5: Invalid coupon kind
@pytest.mark.ac("S3-AC5")
def test_coupon_invalid_kind_raises_error():
    """A coupon whose kind is neither 'percent' nor 'fixed' raises CouponError."""
    catalog = {"SKU-P": Product("SKU-P", "Item P", Decimal("100.00"))}
    lines = [Line("SKU-P", 1)]
    coupon = Coupon("BAD", "invalid", Decimal("10"))
    today = date(2026, 1, 1)
    
    with pytest.raises(CouponError):
        price_cart(lines, catalog, today=today, coupon=coupon)


@pytest.mark.ac("S3-AC5")
def test_coupon_uppercase_percent_raises_error():
    """A coupon with uppercase 'PERCENT' kind raises CouponError."""
    catalog = {"SKU-Q": Product("SKU-Q", "Item Q", Decimal("100.00"))}
    lines = [Line("SKU-Q", 1)]
    coupon = Coupon("BAD", "PERCENT", Decimal("10"))
    today = date(2026, 1, 1)
    
    with pytest.raises(CouponError):
        price_cart(lines, catalog, today=today, coupon=coupon)


@pytest.mark.ac("S3-AC5")
def test_coupon_uppercase_fixed_raises_error():
    """A coupon with uppercase 'FIXED' kind raises CouponError."""
    catalog = {"SKU-R": Product("SKU-R", "Item R", Decimal("100.00"))}
    lines = [Line("SKU-R", 1)]
    coupon = Coupon("BAD", "FIXED", Decimal("10"))
    today = date(2026, 1, 1)
    
    with pytest.raises(CouponError):
        price_cart(lines, catalog, today=today, coupon=coupon)


@pytest.mark.ac("S3-AC5")
def test_coupon_other_invalid_kinds_raise_error():
    """Various other invalid coupon kinds raise CouponError."""
    catalog = {"SKU-S": Product("SKU-S", "Item S", Decimal("100.00"))}
    lines = [Line("SKU-S", 1)]
    today = date(2026, 1, 1)
    
    for invalid_kind in ["buy_one_get_one", "rebate", "discount", "voucher"]:
        coupon = Coupon("BAD", invalid_kind, Decimal("10"))
        with pytest.raises(CouponError):
            price_cart(lines, catalog, today=today, coupon=coupon)
