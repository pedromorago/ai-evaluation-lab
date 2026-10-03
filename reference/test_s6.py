from datetime import date
from decimal import Decimal as D

import pytest

from checkout import Coupon, Customer, Line, Product, price_cart

TODAY = date(2026, 5, 1)
CATALOG = {
    "MUG": Product("MUG", "Mug", D("8.00")),
    "PEN": Product("PEN", "Pen", D("1.25")),
}


def quote(*lines, **kw):
    return price_cart([Line(sku, qty) for sku, qty in lines], CATALOG, today=TODAY, **kw)


@pytest.mark.ac("S6-AC1")
def test_vat_is_21_percent_of_goods_plus_shipping():
    q = quote(("MUG", 2), ("PEN", 3))
    assert (q.shipping, q.tax) == (D("4.99"), D("5.20"))


@pytest.mark.ac("S6-AC2")
def test_total_is_subtotal_minus_discount_plus_shipping_plus_tax():
    q = quote(("MUG", 2), ("PEN", 3))
    assert q.total == q.subtotal - q.discount + q.shipping + q.tax == D("29.94")


@pytest.mark.ac("S6-AC2")
def test_rounding_is_half_up():
    # 50 pens at 15% off come to 53.125: half up gives 53.13, half even would give 53.12
    q = quote(("PEN", 50))
    assert (q.subtotal, q.tax, q.total) == (D("53.13"), D("11.16"), D("64.29"))


@pytest.mark.ac("S6-AC3")
def test_applied_lists_volume_then_rate_discount_then_fixed_coupon():
    q = quote(("PEN", 10), ("MUG", 10), customer=Customer("gold"), coupon=Coupon("OFF", "fixed", D("5")))
    assert q.applied == ("volume:PEN", "volume:MUG", "loyalty", "coupon:OFF")
