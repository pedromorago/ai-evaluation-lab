"""Reference tests for S1, cart lines. Written by hand from the story, like the
generated suites, and used to decide which mutants count."""

from datetime import date
from decimal import Decimal as D

import pytest

from checkout import CartError, Coupon, Customer, Line, Product, price_cart

TODAY = date(2026, 5, 1)
CATALOG = {
    "MUG": Product("MUG", "Mug", D("8.00")),
    "PEN": Product("PEN", "Pen", D("1.25")),
}


def quote(*lines, **kw):
    return price_cart([Line(sku, qty) for sku, qty in lines], CATALOG, today=TODAY, **kw)


@pytest.mark.ac("S1-AC1")
def test_subtotal_adds_unit_price_times_quantity():
    assert quote(("MUG", 2), ("PEN", 3)).subtotal == D("19.75")


@pytest.mark.ac("S1-AC2")
@pytest.mark.parametrize("quantity", [0, -1, 100, 1.5, True, "2"])
def test_bad_quantities_are_rejected(quantity):
    with pytest.raises(CartError):
        quote(("MUG", quantity))


@pytest.mark.ac("S1-AC2")
@pytest.mark.parametrize("quantity, subtotal", [(1, D("8.00")), (99, D("673.20"))])
def test_quantity_boundaries_are_accepted(quantity, subtotal):
    assert quote(("MUG", quantity)).subtotal == subtotal


@pytest.mark.ac("S1-AC3")
def test_unknown_sku_is_rejected():
    with pytest.raises(CartError):
        quote(("MUG", 1), ("NOPE", 1))


@pytest.mark.ac("S1-AC4", "S2-AC1")
def test_lines_with_the_same_sku_are_merged():
    q = quote(("MUG", 5), ("PEN", 1), ("MUG", 5))
    assert q.subtotal == D("73.25")  # 10 mugs at 10% off, plus a pen
    assert q.applied == ("volume:MUG",)


@pytest.mark.ac("S1-AC4")
def test_merged_quantity_may_reach_99():
    assert quote(("PEN", 50), ("PEN", 49)).subtotal == D("105.19")


@pytest.mark.ac("S1-AC4")
def test_merged_quantity_over_99_is_rejected():
    with pytest.raises(CartError):
        quote(("PEN", 60), ("PEN", 40))


@pytest.mark.ac("S1-AC5")
def test_empty_cart_costs_nothing():
    q = quote(
        customer=Customer("gold"),
        coupon=Coupon("BIG", "percent", D("10"), min_subtotal=D("30")),
    )
    assert (q.subtotal, q.discount, q.shipping, q.tax, q.total, q.applied) == (0, 0, 0, 0, 0, ())
