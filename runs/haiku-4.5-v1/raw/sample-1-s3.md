```python
import pytest
from decimal import Decimal
from datetime import date
from checkout import (
    CartError,
    CouponError,
    Product,
    Line,
    Customer,
    Coupon,
    price_cart,
)


@pytest.fixture
def catalog():
    return {
        "WIDGET-A": Product("WIDGET-A", "Widget A", Decimal("10.00")),
        "WIDGET-B": Product("WIDGET-B", "Widget B", Decimal("20.00")),
        "WIDGET-C": Product("WIDGET-C", "Widget C", Decimal("100.00")),
    }


@pytest.fixture
def standard_customer():
    return Customer(tier="standard")


@pytest.fixture
def today():
    return date(2026, 10, 3)


# S3-AC1: Percent coupon
@pytest.mark.ac("S3-AC1")
def test_percent_coupon_10_percent_off_subtotal(catalog, standard_customer, today):
    """Percent coupon with value 10 applies 10% off the subtotal"""
    lines = [Line("WIDGET-A", 1)]
    coupon = Coupon("SAVE10", "percent", Decimal("10"))
    quote = price_cart(lines, catalog, today=today, customer=standard_customer, coupon=coupon)
    assert quote.subtotal == Decimal("10.00")
    assert "coupon:SAVE10" in quote.applied


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_50_percent_off_subtotal(catalog, standard_customer, today):
    """Percent coupon with value 50 applies 50% off the subtotal"""
    lines = [Line("WIDGET-B", 1)]
    coupon = Coupon("HALF", "percent", Decimal("50"))
    quote = price_cart(lines, catalog, today=today, customer=standard_customer, coupon=coupon)
    assert quote.subtotal == Decimal("20.00")
    assert "coupon:HALF" in quote.applied


@pytest.mark.ac("S3-AC1")
def test_percent_coupon_25_percent_off_larger_subtotal(catalog, standard_customer, today):
    """Percent coupon percentage applies to full subtotal"""
    lines = [Line("WIDGET-B", 2)]
    coupon = Coupon("DISCOUNT25", "percent", Decimal("25"))
    quote = price_cart(lines, catalog, today=today, customer=standard_customer, coupon=coupon)
    assert quote.subtotal == Decimal("40.00")
    assert "coupon:DISCOUNT25" in quote.applied


# S3-AC2: Fixed coupon
@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_euros_off_subtotal(catalog, standard_customer, today):
    """Fixed coupon takes its value in euros off the subtotal"""
    lines = [Line("WIDGET-A", 1)]
    coupon = Coupon("EURO5", "fixed", Decimal("5.00"))
    quote = price_cart(lines, catalog, today=today, customer=standard_customer, coupon=coupon)
    assert quote.subtotal == Decimal("10.00")
    assert "coupon:EURO5" in quote.applied


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_larger_euro_amount(catalog, standard_customer, today):
    """Fixed coupon subtracts euros from larger subtotal"""
    lines = [Line("WIDGET-C", 1)]
    coupon = Coupon("EURO25", "fixed", Decimal("25.00"))
    quote = price_cart(lines, catalog, today=today, customer=standard_customer, coupon=coupon)
    assert quote.subtotal == Decimal("100.00")
    assert "coupon:EURO25" in quote.applied


@pytest.mark.ac("S3-AC2")
def test_fixed_coupon_never_takes_below_zero(catalog, standard_customer, today):
    """Fixed coupon never reduces goods below 0.00"""
    lines = [Line("WIDGET-A", 1)]
    coupon = Coupon("TOOBIG", "fixed", Decimal("999.00"))
    quote = price_cart(lines, catalog, today=today, customer=standard_customer, coupon=coupon)
    assert quote.subtotal == Decimal("10.00")
    assert "coupon:TOOBIG" in quote.applied
    assert quote.discount <= quote.subtotal


# S3-AC3: Minimum subtotal
@pytest.mark.ac("S3-AC3")
def test_coupon_min_subtotal_not_met_raises_error(catalog, standard_customer, today):
    """Coupon raises CouponError when subtotal below min_subtotal"""
    lines = [Line("WIDGET-A", 1)]
    coupon = Coupon("MIN50", "percent", Decimal("10"), min_subtotal=Decimal("50.00"))
    with pytest.raises(CouponError):
        price_cart(lines, catalog, today=today, customer=standard_customer, coupon=coupon)


@pytest.mark.ac("S3-AC3")
def test_coupon_min_subtotal_exactly_met_is_valid(catalog, standard_customer, today):
    """Coupon is valid when subtotal equals min_subtotal"""
    lines = [Line("WIDGET-B", 1)]
    coupon = Coupon("MIN20", "percent", Decimal("10"), min_subtotal=Decimal("20.00"))
    quote = price_cart(lines, catalog, today=today, customer=standard_customer, coupon=coupon)
    assert quote.subtotal == Decimal("20.00")
    assert "coupon:MIN20" in quote.applied


@pytest.mark.ac("S3-AC3")
def test_coupon_min_subtotal_exceeded_is_valid(catalog, standard_customer, today):
    """Coupon is valid when subtotal exceeds min_subtotal"""
    lines = [Line("WIDGET-C", 1)]
    coupon = Coupon("MIN50", "percent", Decimal("10"), min_subtotal=Decimal("50.00"))
    quote = price_cart(lines, catalog, today=today, customer=standard_customer, coupon=coupon)
    assert quote.subtotal == Decimal("100.00")
    assert "coupon:MIN50" in quote.applied


# S3-AC4: Expiry date
@pytest.mark.ac("S3-AC4")
def test_coupon_after_expiry_date_raises_error(catalog, standard_customer):
    """Coupon raises CouponError when used after expiry date"""
    lines = [Line("WIDGET-A", 1)]
    coupon = Coupon("EXPIRED", "percent", Decimal("10"), expires=date(2026, 10, 1))
    with pytest.raises(CouponError):
        price_cart(lines, catalog, today=date(2026, 10, 3), customer=standard_customer, coupon=coupon)


@pytest.mark.ac("S3-AC4")
def test_coupon_on_expiry_date_is_valid(catalog, standard_customer):
    """Coupon is valid on the expiry date itself"""
    lines = [Line("WIDGET-A", 1)]
    coupon = Coupon("LASTDAY", "percent", Decimal("10"), expires=date(2026, 10, 3))
    quote = price_cart(lines, catalog, today=date(2026, 10, 3), customer=standard_customer, coupon=coupon)
    assert "coupon:LASTDAY" in quote.applied


@pytest.mark.ac("S3-AC4")
def test_coupon_before_expiry_date_is_valid(catalog, standard_customer):
    """Coupon is valid before expiry date"""
    lines = [Line("WIDGET-A", 1)]
    coupon = Coupon("FUTURE", "percent", Decimal("10"), expires=date(2026, 10, 4))
    quote = price_cart(lines, catalog, today=date(2026, 10, 3), customer=standard_customer, coupon=coupon)
    assert "coupon:FUTURE" in quote.applied


@pytest.mark.ac("S3-AC4")
def test_coupon_without_expiry_date_never_expires(catalog, standard_customer):
    """Coupon without expiry date is always valid"""
    lines = [Line("WIDGET-A", 1)]
    coupon = Coupon("FOREVER", "percent", Decimal("10"), expires=None)
    quote = price_cart(lines, catalog, today=date(2200, 12, 31), customer=standard_customer, coupon=coupon)
    assert "coupon:FOREVER" in quote.applied


# S3-AC5: Invalid coupon kind
@pytest.mark.ac("S3-AC5")
def test_coupon_invalid_kind_buy_one_get_one_raises_error(catalog, standard_customer, today):
    """Coupon with invalid kind raises CouponError"""
    lines = [Line("WIDGET-A", 1)]
    coupon = Coupon("BOGO", "buy_one_get_one", Decimal("0"))
    with pytest.raises(CouponError):
        price_cart(lines, catalog, today=today, customer=standard_customer, coupon=coupon)


@pytest.mark.ac("S3-AC5")
def test_coupon_kind_must_be_percent_or_fixed(catalog, standard_customer, today):
    """Coupon kind must be percent or fixed, not other values"""
    lines = [Line("WIDGET-A", 1)]
    coupon = Coupon("MYSTERY", "mystery_discount", Decimal("10"))
    with pytest.raises(CouponError):
        price_cart(lines, catalog, today=today, customer=standard_customer, coupon=coupon)


def test_coupon_error_is_subclass_of_cart_error():
    """CouponError is a subclass of CartError"""
    assert issubclass(CouponError, CartError)
```