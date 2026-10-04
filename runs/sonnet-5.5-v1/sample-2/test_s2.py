from datetime import date
from decimal import Decimal

import pytest

from checkout import Customer, Line, Product, price_cart

TODAY = date(2026, 1, 15)

CATALOG = {
    "GEN-1": Product(sku="GEN-1", name="Widget", unit_price=Decimal("2.00")),
    "GEN-2": Product(sku="GEN-2", name="Gadget", unit_price=Decimal("3.00")),
    "PEN": Product(sku="PEN", name="Penny item", unit_price=Decimal("0.01")),
    "BK-1": Product(
        sku="BK-1", name="Novel", unit_price=Decimal("10.00"), category="books"
    ),
}


def quote(lines, **kwargs):
    return price_cart(lines, CATALOG, today=TODAY, **kwargs)


@pytest.mark.ac("S2-AC1")
def test_ten_units_get_ten_percent_off():
    q = quote([Line("GEN-1", 10)])
    assert q.subtotal == Decimal("18.00")
    assert q.applied == ("volume:GEN-1",)


@pytest.mark.ac("S2-AC1")
def test_nine_units_get_no_discount():
    q = quote([Line("GEN-1", 9)])
    assert q.subtotal == Decimal("18.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC1")
def test_eleven_units_get_ten_percent_off():
    q = quote([Line("GEN-1", 11)])
    assert q.subtotal == Decimal("19.80")


@pytest.mark.ac("S2-AC1")
def test_49_units_still_get_ten_percent_off():
    q = quote([Line("GEN-1", 49)])
    assert q.subtotal == Decimal("88.20")
    assert q.applied == ("volume:GEN-1",)


@pytest.mark.ac("S2-AC2")
def test_fifty_units_get_fifteen_percent_off_instead():
    q = quote([Line("GEN-1", 50)])
    assert q.subtotal == Decimal("85.00")
    assert q.applied == ("volume:GEN-1",)


@pytest.mark.ac("S2-AC2")
def test_ninety_nine_units_get_fifteen_percent_off():
    q = quote([Line("GEN-1", 99)])
    assert q.subtotal == Decimal("168.30")


@pytest.mark.ac("S2-AC2", "S6-AC2")
def test_discounted_line_total_rounds_half_up():
    # 50 * 0.01 = 0.50; 15% off = 0.425 -> 0.43
    q = quote([Line("PEN", 50)])
    assert q.subtotal == Decimal("0.43")


@pytest.mark.ac("S2-AC1", "S6-AC2")
def test_ten_percent_discount_rounds_to_cent():
    # 10 * 0.01 = 0.10; 10% off = 0.09
    q = quote([Line("PEN", 10)])
    assert q.subtotal == Decimal("0.09")


@pytest.mark.ac("S2-AC1", "S1-AC4")
def test_split_lines_are_merged_before_ten_unit_threshold():
    q = quote([Line("GEN-1", 6), Line("GEN-1", 4)])
    assert q.subtotal == Decimal("18.00")
    assert q.applied == ("volume:GEN-1",)


@pytest.mark.ac("S2-AC2", "S1-AC4")
def test_split_lines_are_merged_before_fifty_unit_threshold():
    q = quote([Line("GEN-1", 30), Line("GEN-1", 20)])
    assert q.subtotal == Decimal("85.00")
    assert q.applied == ("volume:GEN-1",)


@pytest.mark.ac("S2-AC1")
def test_split_lines_below_threshold_get_no_discount():
    q = quote([Line("GEN-1", 5), Line("GEN-1", 4)])
    assert q.subtotal == Decimal("18.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC1")
def test_different_products_are_not_combined_for_threshold():
    q = quote([Line("GEN-1", 5), Line("GEN-2", 5)])
    assert q.subtotal == Decimal("25.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC1")
def test_discount_applies_only_to_the_qualifying_line():
    q = quote([Line("GEN-1", 10), Line("GEN-2", 2)])
    # 18.00 discounted + 6.00 full price
    assert q.subtotal == Decimal("24.00")
    assert q.applied == ("volume:GEN-1",)


@pytest.mark.ac("S2-AC1", "S2-AC2")
def test_each_product_gets_its_own_tier():
    q = quote([Line("GEN-1", 50), Line("GEN-2", 10)])
    # 85.00 (15%) + 27.00 (10%)
    assert q.subtotal == Decimal("112.00")
    assert q.applied == ("volume:GEN-1", "volume:GEN-2")


@pytest.mark.ac("S2-AC3")
def test_books_get_no_discount_at_ten_units():
    q = quote([Line("BK-1", 10)])
    assert q.subtotal == Decimal("100.00")
    assert "volume:BK-1" not in q.applied
    assert q.applied == ()


@pytest.mark.ac("S2-AC3")
def test_books_get_no_discount_at_fifty_units():
    q = quote([Line("BK-1", 50)])
    assert q.subtotal == Decimal("500.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC3", "S1-AC4")
def test_books_split_across_lines_get_no_discount():
    q = quote([Line("BK-1", 30), Line("BK-1", 30)])
    assert q.subtotal == Decimal("600.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC1", "S2-AC3")
def test_books_in_cart_do_not_affect_other_products_discount():
    q = quote([Line("BK-1", 10), Line("GEN-1", 10)])
    assert q.subtotal == Decimal("118.00")
    assert q.applied == ("volume:GEN-1",)


@pytest.mark.ac("S2-AC1", "S6-AC3")
def test_applied_follows_order_of_first_appearance_in_cart():
    q = quote([Line("GEN-2", 10), Line("GEN-1", 10)])
    assert q.applied == ("volume:GEN-2", "volume:GEN-1")


@pytest.mark.ac("S2-AC1", "S6-AC3", "S1-AC4")
def test_applied_order_uses_first_appearance_after_merging():
    q = quote([Line("GEN-1", 5), Line("GEN-2", 10), Line("GEN-1", 5)])
    assert q.applied == ("volume:GEN-1", "volume:GEN-2")


@pytest.mark.ac("S2-AC1", "S4-AC1")
def test_volume_discount_is_part_of_subtotal_before_loyalty():
    q = quote([Line("GEN-1", 10)], customer=Customer(tier="gold"))
    # Subtotal already includes volume discount; loyalty is reported separately.
    assert q.subtotal == Decimal("18.00")
    assert q.discount == Decimal("0.90")
    assert q.applied == ("volume:GEN-1", "loyalty")
