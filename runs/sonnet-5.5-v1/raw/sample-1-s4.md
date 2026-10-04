```python
from datetime import date
from decimal import Decimal

import pytest

from checkout import (
    Coupon,
    Customer,
    Line,
    Product,
    price_cart,
)

TODAY = date(2026, 1, 15)

CATALOG = {
    "P100": Product("P100", "Hundred", Decimal("100.00")),
    "P52": Product("P52", "FiftyTwo", Decimal("52.00")),
    "P53": Product("P53", "FiftyThree", Decimal("53.00")),
    "P20": Product("P20", "Twenty", Decimal("20.00")),
    "P10": Product("P10", "Ten", Decimal("10.00")),
    "P1010": Product("P1010", "Odd", Decimal("10.10")),
    "BK20": Product("BK20", "Book", Decimal("20.00"), category="books"),
}

GOLD = Customer(tier="gold")
STANDARD = Customer(tier="standard")


def quote(lines, customer=STANDARD, coupon=None, shipping="standard"):
    return price_cart(
        lines,
        CATALOG,
        today=TODAY,
        customer=customer,
        coupon=coupon,
        shipping=shipping,
    )


def pct(code, value):
    return Coupon(code=code, kind="percent", value=Decimal(value))


def fixed(code, value):
    return Coupon(code=code, kind="fixed", value=Decimal(value))


@pytest.mark.ac("S4-AC1")
def test_gold_gets_five_percent_off_full_quote():
    q = quote([Line("P100", 1)], customer=GOLD)
    assert q.subtotal == Decimal("100.00")
    assert q.discount == Decimal("5.00")
    assert q.shipping == Decimal("0.00")
    assert q.tax == Decimal("19.95")
    assert q.total == Decimal("114.95")
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S4-AC1")
def test_standard_gets_no_loyalty_discount():
    q = quote([Line("P100", 1)], customer=STANDARD)
    assert q.subtotal == Decimal("100.00")
    assert q.discount == Decimal("0.00")
    assert q.applied == ()
    assert q.total == Decimal("121.00")


@pytest.mark.ac("S4-AC1")
def test_default_customer_is_standard_no_loyalty():
    q = price_cart([Line("P100", 1)], CATALOG, today=TODAY)
    assert q.discount == Decimal("0.00")
    assert q.applied == ()


@pytest.mark.ac("S4-AC1")
def test_loyalty_discount_rounded_half_up():
    # 5% of 10.10 = 0.505 -> 0.51
    q = quote([Line("P1010", 1)], customer=GOLD)
    assert q.subtotal == Decimal("10.10")
    assert q.discount == Decimal("0.51")
    assert q.total == q.subtotal - q.discount + q.shipping + q.tax


@pytest.mark.ac("S4-AC1")
def test_loyalty_applies_to_books():
    q = quote([Line("BK20", 1)], customer=GOLD)
    assert q.subtotal == Decimal("20.00")
    assert q.discount == Decimal("1.00")
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S4-AC1")
def test_loyalty_is_taken_on_subtotal_after_volume_discount():
    # 10 x 10.00 = 100.00, volume 10% -> 90.00 ; loyalty 5% of 90.00 = 4.50
    q = quote([Line("P10", 10)], customer=GOLD)
    assert q.subtotal == Decimal("90.00")
    assert q.discount == Decimal("4.50")
    assert q.applied == ("volume:P10", "loyalty")


@pytest.mark.ac("S4-AC1")
def test_loyalty_discount_can_remove_free_shipping():
    standard = quote([Line("P52", 1)], customer=STANDARD)
    gold = quote([Line("P52", 1)], customer=GOLD)
    # standard: goods 52.00 -> free shipping
    assert standard.shipping == Decimal("0.00")
    # gold: 52.00 - 2.60 = 49.40 -> shipping charged
    assert gold.discount == Decimal("2.60")
    assert gold.shipping == Decimal("4.99")


@pytest.mark.ac("S4-AC1")
def test_gold_still_gets_free_shipping_when_goods_after_loyalty_reach_50():
    # 53.00 - 2.65 = 50.35
    q = quote([Line("P53", 1)], customer=GOLD)
    assert q.discount == Decimal("2.65")
    assert q.shipping == Decimal("0.00")


@pytest.mark.ac("S4-AC2")
def test_larger_percent_coupon_wins_over_loyalty():
    q = quote([Line("P100", 1)], customer=GOLD, coupon=pct("SAVE10", "10"))
    assert q.discount == Decimal("10.00")
    assert q.tax == Decimal("18.90")
    assert q.total == Decimal("108.90")
    assert q.applied == ("coupon:SAVE10",)


@pytest.mark.ac("S4-AC2")
def test_larger_loyalty_wins_over_smaller_percent_coupon():
    q = quote([Line("P100", 1)], customer=GOLD, coupon=pct("SAVE3", "3"))
    assert q.discount == Decimal("5.00")
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S4-AC2")
def test_equal_percent_coupon_wins_tie_over_loyalty():
    q = quote([Line("P100", 1)], customer=GOLD, coupon=pct("FIVE", "5"))
    assert q.discount == Decimal("5.00")
    assert q.applied == ("coupon:FIVE",)


@pytest.mark.ac("S4-AC2")
def test_percent_coupon_and_loyalty_never_add_up():
    q = quote([Line("P100", 1)], customer=GOLD, coupon=pct("SAVE10", "10"))
    assert q.discount != Decimal("15.00")
    assert "loyalty" not in q.applied


@pytest.mark.ac("S4-AC2")
def test_standard_customer_with_percent_coupon_gets_coupon_only():
    q = quote([Line("P100", 1)], customer=STANDARD, coupon=pct("SAVE3", "3"))
    assert q.discount == Decimal("3.00")
    assert q.applied == ("coupon:SAVE3",)


@pytest.mark.ac("S4-AC2")
def test_fixed_coupon_stacks_with_loyalty():
    q = quote([Line("P100", 1)], customer=GOLD, coupon=fixed("FIX10", "10"))
    # loyalty 5.00, then 10.00 off
    assert q.subtotal == Decimal("100.00")
    assert q.discount == Decimal("15.00")
    assert q.shipping == Decimal("0.00")
    assert q.tax == Decimal("18.90")
    assert q.total == Decimal("103.90")
    assert q.applied == ("loyalty", "fixed_placeholder") or q.applied == (
        "loyalty",
        "coupon:FIX10",
    )
    assert q.applied == ("loyalty", "coupon:FIX10")


@pytest.mark.ac("S4-AC2")
def test_fixed_coupon_alone_for_standard_customer():
    q = quote([Line("P100", 1)], customer=STANDARD, coupon=fixed("FIX10", "10"))
    assert q.discount == Decimal("10.00")
    assert q.applied == ("coupon:FIX10",)


@pytest.mark.ac("S4-AC2")
def test_fixed_coupon_is_taken_after_loyalty_and_capped_at_remaining_goods():
    # subtotal 20.00, loyalty 1.00 -> 19.00 left; fixed 50 is capped at 19.00
    q = quote([Line("P20", 1)], customer=GOLD, coupon=fixed("BIG", "50"))
    assert q.subtotal == Decimal("20.00")
    assert q.discount == Decimal("20.00")
    assert q.shipping == Decimal("4.99")
    assert q.tax == Decimal("1.05")
    assert q.total == Decimal("6.04")
    assert q.applied == ("loyalty", "coupon:BIG")


@pytest.mark.ac("S4-AC2")
def test_applied_order_volume_then_loyalty_then_fixed_coupon():
    q = quote([Line("P10", 10)], customer=GOLD, coupon=fixed("FIX5", "5"))
    # subtotal 90.00, loyalty 4.50, fixed 5.00
    assert q.subtotal == Decimal("90.00")
    assert q.discount == Decimal("9.50")
    assert q.applied == ("volume:P10", "loyalty", "coupon:FIX5")


@pytest.mark.ac("S4-AC2")
def test_applied_order_volume_then_winning_percent_coupon():
    q = quote([Line("P10", 10)], customer=GOLD, coupon=pct("SAVE20", "20"))
    assert q.subtotal == Decimal("90.00")
    assert q.discount == Decimal("18.00")
    assert q.applied == ("volume:P10", "coupon:SAVE20")


@pytest.mark.ac("S4-AC2")
def test_quote_total_identity_with_loyalty_and_fixed_coupon():
    q = quote([Line("P1010", 3)], customer=GOLD, coupon=fixed("FIX1", "1"))
    assert q.total == q.subtotal - q.discount + q.shipping + q.tax
```