from datetime import date
from decimal import Decimal

import pytest

from checkout import Coupon, Customer, Line, Product, price_cart

TODAY = date(2026, 1, 15)

CATALOG = {
    "A": Product(sku="A", name="Item A", unit_price=Decimal("100.00")),
    "CHEAP": Product(sku="CHEAP", name="Cheap", unit_price=Decimal("20.00")),
    "ODD": Product(sku="ODD", name="Odd price", unit_price=Decimal("10.10")),
    "TEN": Product(sku="TEN", name="Ten euro", unit_price=Decimal("10.00")),
    "MID": Product(sku="MID", name="Mid", unit_price=Decimal("52.00")),
}

GOLD = Customer(tier="gold")
STANDARD = Customer(tier="standard")


def pct(code, value):
    return Coupon(code=code, kind="percent", value=Decimal(value))


def fixed(code, value):
    return Coupon(code=code, kind="fixed", value=Decimal(value))


def quote(lines, customer=STANDARD, coupon=None, shipping="standard"):
    return price_cart(
        lines,
        CATALOG,
        today=TODAY,
        customer=customer,
        coupon=coupon,
        shipping=shipping,
    )


@pytest.mark.ac("S4-AC1")
def test_gold_gets_five_percent_off():
    q = quote([Line("A", 1)], customer=GOLD)
    assert q.subtotal == Decimal("100.00")
    assert q.discount == Decimal("5.00")
    assert q.shipping == Decimal("0.00")
    assert q.tax == Decimal("19.95")
    assert q.total == Decimal("114.95")
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S4-AC1")
def test_standard_gets_no_loyalty_discount():
    q = quote([Line("A", 1)], customer=STANDARD)
    assert q.subtotal == Decimal("100.00")
    assert q.discount == Decimal("0.00")
    assert q.tax == Decimal("21.00")
    assert q.total == Decimal("121.00")
    assert q.applied == ()


@pytest.mark.ac("S4-AC1")
def test_default_customer_is_standard_without_loyalty():
    q = price_cart([Line("A", 1)], CATALOG, today=TODAY)
    assert q.discount == Decimal("0.00")
    assert "loyalty" not in q.applied


@pytest.mark.ac("S4-AC1")
def test_gold_loyalty_discount_rounds_half_up():
    # 5% of 10.10 = 0.505 -> 0.51
    q = quote([Line("ODD", 1)], customer=GOLD)
    assert q.subtotal == Decimal("10.10")
    assert q.discount == Decimal("0.51")
    assert q.shipping == Decimal("4.99")
    assert q.tax == Decimal("3.06")
    assert q.total == Decimal("17.64")


@pytest.mark.ac("S4-AC1")
def test_loyalty_applies_to_subtotal_after_volume_discount():
    # 10 x 10.00 = 100 - 10% = 90.00 subtotal; loyalty 5% of 90 = 4.50
    q = quote([Line("TEN", 10)], customer=GOLD)
    assert q.subtotal == Decimal("90.00")
    assert q.discount == Decimal("4.50")
    assert q.shipping == Decimal("0.00")
    assert q.tax == Decimal("17.96")
    assert q.total == Decimal("103.46")
    assert q.applied == ("volume:TEN", "loyalty")


@pytest.mark.ac("S4-AC1")
def test_loyalty_discount_counts_toward_free_shipping_threshold():
    # 52.00 - 5% (2.60) = 49.40 < 50.00, so shipping is charged
    q = quote([Line("MID", 1)], customer=GOLD)
    assert q.subtotal == Decimal("52.00")
    assert q.discount == Decimal("2.60")
    assert q.shipping == Decimal("4.99")


@pytest.mark.ac("S4-AC1", "S1-AC5")
def test_empty_cart_ignores_gold_tier():
    q = quote([], customer=GOLD)
    assert q.subtotal == Decimal("0.00")
    assert q.discount == Decimal("0.00")
    assert q.shipping == Decimal("0.00")
    assert q.tax == Decimal("0.00")
    assert q.total == Decimal("0.00")
    assert q.applied == ()


@pytest.mark.ac("S4-AC2")
def test_larger_percent_coupon_beats_loyalty():
    q = quote([Line("A", 1)], customer=GOLD, coupon=pct("SAVE10", "10"))
    assert q.discount == Decimal("10.00")
    assert q.applied == ("coupon:SAVE10",)
    assert q.tax == Decimal("18.90")
    assert q.total == Decimal("108.90")


@pytest.mark.ac("S4-AC2")
def test_larger_loyalty_beats_smaller_percent_coupon():
    q = quote([Line("A", 1)], customer=GOLD, coupon=pct("SAVE3", "3"))
    assert q.discount == Decimal("5.00")
    assert q.applied == ("loyalty",)
    assert q.total == Decimal("114.95")


@pytest.mark.ac("S4-AC2")
def test_equal_percent_coupon_and_loyalty_applies_coupon_only():
    q = quote([Line("A", 1)], customer=GOLD, coupon=pct("FIVE", "5"))
    assert q.discount == Decimal("5.00")
    assert q.applied == ("coupon:FIVE",)
    assert q.total == Decimal("114.95")


@pytest.mark.ac("S4-AC2")
def test_percent_coupon_and_loyalty_do_not_stack():
    q = quote([Line("A", 1)], customer=GOLD, coupon=pct("SAVE10", "10"))
    # stacked would be 15.00
    assert q.discount != Decimal("15.00")
    assert q.discount == Decimal("10.00")


@pytest.mark.ac("S4-AC2")
def test_standard_customer_percent_coupon_unaffected():
    q = quote([Line("A", 1)], customer=STANDARD, coupon=pct("SAVE3", "3"))
    assert q.discount == Decimal("3.00")
    assert q.applied == ("coupon:SAVE3",)


@pytest.mark.ac("S4-AC2")
def test_fixed_coupon_stacks_with_loyalty():
    q = quote([Line("A", 1)], customer=GOLD, coupon=fixed("FIX10", "10"))
    assert q.subtotal == Decimal("100.00")
    assert q.discount == Decimal("15.00")
    assert q.shipping == Decimal("0.00")
    assert q.tax == Decimal("17.85")
    assert q.total == Decimal("102.85")
    assert q.applied == ("loyalty", "coupon:FIX10")


@pytest.mark.ac("S4-AC2")
def test_standard_customer_fixed_coupon_has_no_loyalty():
    q = quote([Line("A", 1)], customer=STANDARD, coupon=fixed("FIX10", "10"))
    assert q.discount == Decimal("10.00")
    assert q.applied == ("coupon:FIX10",)


@pytest.mark.ac("S4-AC2")
def test_fixed_coupon_is_taken_off_after_loyalty_and_cannot_go_below_zero():
    # 20.00 - 1.00 loyalty = 19.00 left; fixed 25 can only take 19.00
    q = quote([Line("CHEAP", 1)], customer=GOLD, coupon=fixed("BIG", "25"))
    assert q.subtotal == Decimal("20.00")
    assert q.discount == Decimal("20.00")
    assert q.shipping == Decimal("4.99")
    assert q.tax == Decimal("1.05")
    assert q.total == Decimal("6.04")
    assert q.applied == ("loyalty", "coupon:BIG")


@pytest.mark.ac("S4-AC2")
def test_applied_order_volume_then_loyalty_then_fixed_coupon():
    q = quote([Line("TEN", 10)], customer=GOLD, coupon=fixed("FIX5", "5"))
    # subtotal 90.00, loyalty 4.50, fixed 5.00 -> discount 9.50, goods 80.50
    assert q.subtotal == Decimal("90.00")
    assert q.discount == Decimal("9.50")
    assert q.shipping == Decimal("0.00")
    assert q.tax == Decimal("16.91")
    assert q.total == Decimal("97.41")
    assert q.applied == ("volume:TEN", "loyalty", "coupon:FIX5")


@pytest.mark.ac("S4-AC2")
def test_applied_order_volume_then_winning_percent_coupon():
    q = quote([Line("TEN", 10)], customer=GOLD, coupon=pct("SAVE10", "10"))
    # subtotal 90.00, coupon 10% = 9.00 beats loyalty 4.50
    assert q.discount == Decimal("9.00")
    assert q.applied == ("volume:TEN", "coupon:SAVE10")
