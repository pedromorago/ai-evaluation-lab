from datetime import date
from decimal import Decimal as D

import pytest

from checkout import Line, Product, price_cart

TODAY = date(2026, 5, 1)
CATALOG = {
    "MUG": Product("MUG", "Mug", D("8.00")),
    "PEN": Product("PEN", "Pen", D("1.25")),
    "BOOK": Product("BOOK", "Book", D("12.00"), "books"),
}


def quote(*lines, **kw):
    return price_cart([Line(sku, qty) for sku, qty in lines], CATALOG, today=TODAY, **kw)


@pytest.mark.ac("S2-AC1")
def test_ten_units_take_ten_percent_off():
    q = quote(("MUG", 10))
    assert q.subtotal == D("72.00")
    assert q.applied == ("volume:MUG",)


@pytest.mark.ac("S2-AC1")
def test_nine_units_pay_full_price():
    q = quote(("MUG", 9))
    assert q.subtotal == D("72.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC2")
@pytest.mark.parametrize("quantity, subtotal", [(49, D("55.13")), (50, D("53.13"))])
def test_fifty_units_take_fifteen_percent_off(quantity, subtotal):
    assert quote(("PEN", quantity)).subtotal == subtotal


@pytest.mark.ac("S2-AC1", "S2-AC2")
def test_discount_applies_per_line_not_per_cart():
    q = quote(("MUG", 10), ("PEN", 9))
    assert q.subtotal == D("83.25")
    assert q.applied == ("volume:MUG",)


@pytest.mark.ac("S2-AC3")
@pytest.mark.parametrize("quantity", [10, 50])
def test_books_never_get_a_volume_discount(quantity):
    q = quote(("BOOK", quantity))
    assert q.subtotal == D("12.00") * quantity
    assert q.applied == ()
