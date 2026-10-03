from datetime import date
from decimal import Decimal as D

import pytest

from checkout import CartError, Coupon, Line, Product, price_cart

TODAY = date(2026, 5, 1)
CATALOG = {
    "MUG": Product("MUG", "Mug", D("8.00")),
    "PEN": Product("PEN", "Pen", D("1.25")),
    "LAMP": Product("LAMP", "Lamp", D("45.00")),
}


def quote(*lines, **kw):
    return price_cart([Line(sku, qty) for sku, qty in lines], CATALOG, today=TODAY, **kw)


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_below_fifty():
    assert quote(("MUG", 6), ("PEN", 1)).shipping == D("4.99")


@pytest.mark.ac("S5-AC1")
def test_standard_shipping_is_free_from_fifty():
    assert quote(("MUG", 5), ("PEN", 8)).shipping == D("0.00")


@pytest.mark.ac("S5-AC1")
def test_free_shipping_looks_at_the_goods_after_discounts():
    q = quote(("LAMP", 2), coupon=Coupon("OFF", "fixed", D("41")))
    assert q.shipping == D("4.99")
    assert quote(("LAMP", 2), coupon=Coupon("TEN", "percent", D("10"))).shipping == D("0.00")


@pytest.mark.ac("S5-AC2")
def test_express_costs_the_same_and_is_never_free():
    assert quote(("MUG", 1), shipping="express").shipping == D("9.99")
    assert quote(("LAMP", 3), shipping="express").shipping == D("9.99")


@pytest.mark.ac("S5-AC3")
def test_unknown_shipping_method_is_rejected():
    with pytest.raises(CartError):
        quote(("MUG", 1), shipping="drone")
