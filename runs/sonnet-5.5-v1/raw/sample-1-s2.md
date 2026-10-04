```python
import pytest
from datetime import date
from decimal import Decimal

from checkout import Line, Product, price_cart

TODAY = date(2026, 1, 15)

CATALOG = {
    "GEN-1": Product("GEN-1", "Widget", Decimal("10.00")),
    "GEN-2": Product("GEN-2", "Gadget", Decimal("2.00")),
    "GEN-3": Product("GEN-3", "Gizmo", Decimal("5.00")),
    "PENNY": Product("PENNY", "Penny item", Decimal("0.01")),
    "BK-1": Product("BK-1", "Novel", Decimal("10.00"), category="books"),
    "BK-2": Product("BK-2", "Atlas", Decimal("2.00"), category="books"),
}


def quote(lines):
    return price_cart(lines, CATALOG, today=TODAY)


@pytest.mark.ac("S2-AC1")
def test_nine_units_get_no_discount():
    q = quote([Line("GEN-1", 9)])
    assert q.subtotal == Decimal("90.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC1")
def test_ten_units_get_ten_percent_off():
    q = quote([Line("GEN-1", 10)])
    assert q.subtotal == Decimal("90.00")
    assert q.applied == ("volume:GEN-1",)


@pytest.mark.ac("S2-AC1")
def test_eleven_units_get_ten_percent_off():
    q = quote([Line("GEN-1", 11)])
    assert q.subtotal == Decimal("99.00")
    assert q.applied == ("volume:GEN-1",)


@pytest.mark.ac("S2-AC1")
def test_forty_nine_units_still_ten_percent():
    q = quote([Line("GEN-2", 49)])
    assert q.subtotal == Decimal("88.20")
    assert q.applied == ("volume:GEN-2",)


@pytest.mark.ac("S2-AC2")
def test_fifty_units_get_fifteen_percent_off_instead():
    q = quote([Line("GEN-2", 50)])
    assert q.subtotal == Decimal("85.00")
    assert q.applied == ("volume:GEN-2",)


@pytest.mark.ac("S2-AC2")
def test_ninety_nine_units_get_fifteen_percent_off():
    q = quote([Line("GEN-2", 99)])
    assert q.subtotal == Decimal("168.30")
    assert q.applied == ("volume:GEN-2",)


@pytest.mark.ac("S2-AC1", "S1-AC4")
def test_split_lines_are_merged_to_reach_ten_percent_tier():
    q = quote([Line("GEN-1", 5), Line("GEN-1", 5)])
    assert q.subtotal == Decimal("90.00")
    assert q.applied == ("volume:GEN-1",)


@pytest.mark.ac("S2-AC1", "S1-AC4")
def test_split_lines_below_threshold_get_no_discount():
    q = quote([Line("GEN-1", 5), Line("GEN-1", 4)])
    assert q.subtotal == Decimal("90.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC2", "S1-AC4")
def test_split_lines_are_merged_to_reach_fifteen_percent_tier():
    q = quote([Line("GEN-2", 40), Line("GEN-2", 10)])
    assert q.subtotal == Decimal("85.00")
    assert q.applied == ("volume:GEN-2",)


@pytest.mark.ac("S2-AC1")
def test_threshold_is_per_product_not_per_cart():
    q = quote([Line("GEN-1", 5), Line("GEN-2", 5), Line("GEN-3", 5)])
    assert q.subtotal == Decimal("85.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC1")
def test_only_the_qualifying_line_is_discounted():
    q = quote([Line("GEN-1", 10), Line("GEN-3", 3)])
    assert q.subtotal == Decimal("105.00")
    assert q.applied == ("volume:GEN-1",)


@pytest.mark.ac("S2-AC1", "S2-AC2")
def test_different_tiers_for_different_products_in_one_cart():
    q = quote([Line("GEN-1", 10), Line("GEN-2", 50)])
    assert q.subtotal == Decimal("175.00")
    assert q.applied == ("volume:GEN-1", "volume:GEN-2")


@pytest.mark.ac("S2-AC3")
@pytest.mark.parametrize("qty", [10, 49, 50, 99])
def test_books_never_get_volume_discount(qty):
    q = quote([Line("BK-1", qty)])
    assert q.subtotal == Decimal("10.00") * qty
    assert q.applied == ()


@pytest.mark.ac("S2-AC3", "S1-AC4")
def test_books_split_lines_merged_still_no_discount():
    q = quote([Line("BK-1", 30), Line("BK-1", 30)])
    assert q.subtotal == Decimal("600.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC1", "S2-AC3")
def test_books_in_cart_do_not_affect_other_product_discount():
    q = quote([Line("BK-1", 10), Line("GEN-1", 10)])
    assert q.subtotal == Decimal("190.00")
    assert q.applied == ("volume:GEN-1",)


@pytest.mark.ac("S2-AC1", "S2-AC3")
def test_volume_discount_does_not_count_as_coupon_or_loyalty_discount():
    q = quote([Line("GEN-1", 10)])
    assert q.discount == Decimal("0.00")


@pytest.mark.ac("S2-AC1", "S2-AC2")
def test_applied_order_follows_first_appearance_in_cart():
    q = quote([Line("GEN-2", 50), Line("GEN-1", 10), Line("GEN-3", 1)])
    assert q.applied == ("volume:GEN-2", "volume:GEN-1")


@pytest.mark.ac("S2-AC1", "S1-AC4")
def test_applied_order_uses_first_appearance_of_merged_product():
    q = quote(
        [Line("GEN-1", 4), Line("GEN-2", 50), Line("BK-1", 20), Line("GEN-1", 6)]
    )
    assert q.applied == ("volume:GEN-1", "volume:GEN-2")
    assert q.subtotal == Decimal("90.00") + Decimal("85.00") + Decimal("200.00")


@pytest.mark.ac("S2-AC2")
def test_fifteen_percent_discount_rounds_half_up():
    # 50 * 0.01 = 0.50; 15% off = 0.425 -> 0.43
    q = quote([Line("PENNY", 50)])
    assert q.subtotal == Decimal("0.43")


@pytest.mark.ac("S2-AC1")
def test_ten_percent_discount_rounds_half_up():
    # 10 * 0.01 = 0.10; 10% off = 0.09 exactly
    q = quote([Line("PENNY", 10)])
    assert q.subtotal == Decimal("0.09")
```