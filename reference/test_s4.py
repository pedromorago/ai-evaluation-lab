from datetime import date
from decimal import Decimal as D

import pytest

from checkout import Coupon, Customer, Line, Product, price_cart

TODAY = date(2026, 5, 1)
CATALOG = {
    "MUG": Product("MUG", "Mug", D("8.00")),
    "TEA": Product("TEA", "Tea", D("3.70")),
    "LAMP": Product("LAMP", "Lamp", D("45.00")),
}
GOLD = Customer("gold")


def quote(*lines, **kw):
    return price_cart([Line(sku, qty) for sku, qty in lines], CATALOG, today=TODAY, **kw)


@pytest.mark.ac("S4-AC1")
def test_gold_customers_get_five_percent_off():
    q = quote(("LAMP", 1), customer=GOLD)
    assert (q.discount, q.applied) == (D("2.25"), ("loyalty",))


@pytest.mark.ac("S4-AC1")
def test_standard_customers_get_no_loyalty_discount():
    q = quote(("LAMP", 1), customer=Customer("standard"))
    assert (q.discount, q.applied) == (D("0.00"), ())


@pytest.mark.ac("S4-AC1", "S6-AC2")
def test_loyalty_discount_is_rounded_before_the_total():
    q = quote(("MUG", 2), ("TEA", 1), customer=GOLD)
    assert (q.subtotal, q.discount, q.tax, q.total) == (D("19.70"), D("0.99"), D("4.98"), D("28.68"))


@pytest.mark.ac("S4-AC2")
def test_larger_percent_coupon_beats_loyalty():
    q = quote(("LAMP", 2), customer=GOLD, coupon=Coupon("TEN", "percent", D("10")))
    assert (q.discount, q.applied) == (D("9.00"), ("coupon:TEN",))


@pytest.mark.ac("S4-AC2")
def test_larger_loyalty_beats_percent_coupon():
    q = quote(("LAMP", 2), customer=GOLD, coupon=Coupon("TWO", "percent", D("2")))
    assert (q.discount, q.applied) == (D("4.50"), ("loyalty",))


@pytest.mark.ac("S4-AC2")
def test_coupon_wins_a_tie():
    q = quote(("LAMP", 2), customer=GOLD, coupon=Coupon("FIVE", "percent", D("5")))
    assert (q.discount, q.applied) == (D("4.50"), ("coupon:FIVE",))


@pytest.mark.ac("S4-AC2")
def test_fixed_coupon_stacks_with_loyalty():
    q = quote(("LAMP", 2), customer=GOLD, coupon=Coupon("OFF", "fixed", D("5")))
    assert (q.discount, q.applied) == (D("9.50"), ("loyalty", "coupon:OFF"))
