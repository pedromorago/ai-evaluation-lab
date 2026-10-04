from datetime import date
from decimal import Decimal

import pytest

from checkout import Customer, Line, Product, price_cart

TODAY = date(2026, 1, 15)


def D(value):
    return Decimal(value)


def general(sku="A", price="10.00"):
    return Product(sku=sku, name=f"Product {sku}", unit_price=D(price), category="general")


def book(sku="BK-1", price="10.00"):
    return Product(sku=sku, name=f"Book {sku}", unit_price=D(price), category="books")


def quote_for(lines, products):
    catalog = {p.sku: p for p in products}
    return price_cart(lines, catalog, today=TODAY)


# ---------------------------------------------------------------- S2-AC1

@pytest.mark.ac("S2-AC1")
def test_nine_units_get_no_volume_discount():
    # 9 x 10.00 = 90.00, below the 10-unit threshold, so no discount.
    q = quote_for([Line("A", 9)], [general()])
    assert q.subtotal == D("90.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC1")
def test_ten_units_get_ten_percent_off():
    # 10 x 10.00 = 100.00; 10% off -> 100.00 * 0.90 = 90.00
    q = quote_for([Line("A", 10)], [general()])
    assert q.subtotal == D("90.00")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC1")
def test_eleven_units_get_ten_percent_off():
    # 11 x 10.00 = 110.00; 10% off -> 110.00 * 0.90 = 99.00
    q = quote_for([Line("A", 11)], [general()])
    assert q.subtotal == D("99.00")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC1")
def test_with_ten_percent_tier_applies_on_cent_prices():
    # 10 x 19.99 = 199.90; 10% off -> 199.90 * 0.90 = 179.91
    q = quote_for([Line("A", 10)], [general(price="19.99")])
    assert q.subtotal == D("179.91")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC1")
def test_forty_nine_units_still_get_ten_percent_not_fifteen():
    # 49 x 10.00 = 490.00; 10% off -> 490.00 * 0.90 = 441.00
    q = quote_for([Line("A", 49)], [general()])
    assert q.subtotal == D("441.00")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC1")
def test_full_quote_for_ten_units_of_one_product():
    # subtotal: 10 x 10.00 = 100.00; 10% off -> 90.00
    # discount: no coupon, standard customer -> 0.00
    # shipping: standard, goods 90.00 >= 50.00 -> free -> 0.00
    # tax: 21% of (90.00 - 0.00 + 0.00) = 18.90
    # total: 90.00 - 0.00 + 0.00 + 18.90 = 108.90
    q = quote_for([Line("A", 10)], [general()])
    assert q.subtotal == D("90.00")
    assert q.discount == D("0.00")
    assert q.shipping == D("0.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")
    assert q.applied == ("volume:A",)


# ---------------------------------------------------------------- S2-AC2

@pytest.mark.ac("S2-AC2")
def test_fifty_units_get_fifteen_percent_off():
    # 50 x 10.00 = 500.00; 15% off -> 500.00 * 0.85 = 425.00
    q = quote_for([Line("A", 50)], [general()])
    assert q.subtotal == D("425.00")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC2")
def test_fifty_units_do_not_stack_ten_and_fifteen_percent():
    # 50 x 20.00 = 1000.00; 15% off instead of 10% -> 1000.00 * 0.85 = 850.00
    # (stacking would give 765.00, a 10% only discount would give 900.00)
    q = quote_for([Line("A", 50)], [general(price="20.00")])
    assert q.subtotal == D("850.00")


@pytest.mark.ac("S2-AC2")
def test_fifty_one_units_get_fifteen_percent_off():
    # 51 x 10.00 = 510.00; 15% off -> 510.00 * 0.85 = 433.50
    q = quote_for([Line("A", 51)], [general()])
    assert q.subtotal == D("433.50")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC2")
def test_ninety_nine_units_get_fifteen_percent_off():
    # 99 x 10.00 = 990.00; 15% off -> 990.00 * 0.85 = 841.50
    q = quote_for([Line("A", 99)], [general()])
    assert q.subtotal == D("841.50")
    assert q.applied == ("volume:A",)


# ---------------------------------------------------------------- S2-AC3

@pytest.mark.ac("S2-AC3")
def test_books_get_no_discount_at_ten_units():
    # 10 x 10.00 = 100.00, books never discounted -> 100.00
    q = quote_for([Line("BK-1", 10)], [book()])
    assert q.subtotal == D("100.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC3")
def test_books_get_no_discount_at_fifty_units():
    # 50 x 10.00 = 500.00, books never discounted -> 500.00
    q = quote_for([Line("BK-1", 50)], [book()])
    assert q.subtotal == D("500.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC3")
def test_books_get_no_discount_at_ninety_nine_units():
    # 99 x 10.00 = 990.00, books never discounted -> 990.00
    q = quote_for([Line("BK-1", 99)], [book()])
    assert q.subtotal == D("990.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC3", "S2-AC1")
def test_book_in_cart_does_not_block_discount_on_general_product():
    # Book: 10 x 10.00 = 100.00 (no discount)
    # General: 10 x 10.00 = 100.00; 10% off -> 90.00
    # subtotal: 100.00 + 90.00 = 190.00
    q = quote_for(
        [Line("BK-1", 10), Line("A", 10)],
        [book(), general()],
    )
    assert q.subtotal == D("190.00")
    assert q.applied == ("volume:A",)


# ------------------------------------------------ merging and per-line scope

@pytest.mark.ac("S2-AC1")
def test_split_lines_are_merged_before_ten_unit_threshold():
    # 6 + 4 = 10 units of A; 10 x 10.00 = 100.00; 10% off -> 90.00
    q = quote_for([Line("A", 6), Line("A", 4)], [general()])
    assert q.subtotal == D("90.00")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC1")
def test_split_lines_totalling_nine_units_get_no_discount():
    # 5 + 4 = 9 units of A; 9 x 10.00 = 90.00; no discount
    q = quote_for([Line("A", 5), Line("A", 4)], [general()])
    assert q.subtotal == D("90.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC2")
def test_split_lines_are_merged_before_fifty_unit_threshold():
    # 30 + 20 = 50 units of A; 50 x 10.00 = 500.00; 15% off -> 425.00
    q = quote_for([Line("A", 30), Line("A", 20)], [general()])
    assert q.subtotal == D("425.00")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC2")
def test_split_lines_totalling_forty_nine_units_get_ten_percent():
    # 30 + 19 = 49 units of A; 49 x 10.00 = 490.00; 10% off -> 441.00
    q = quote_for([Line("A", 30), Line("A", 19)], [general()])
    assert q.subtotal == D("441.00")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC1", "S2-AC2")
def test_discount_only_applies_to_the_product_reaching_the_threshold():
    # A: 10 x 10.00 = 100.00; 10% off -> 90.00
    # B: 5 x 4.00 = 20.00; no discount
    # subtotal: 90.00 + 20.00 = 110.00
    q = quote_for(
        [Line("A", 10), Line("B", 5)],
        [general("A", "10.00"), general("B", "4.00")],
    )
    assert q.subtotal == D("110.00")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC1", "S2-AC2")
def test_each_product_gets_its_own_tier():
    # A: 10 x 10.00 = 100.00; 10% off -> 90.00
    # B: 50 x 2.00 = 100.00; 15% off -> 85.00
    # subtotal: 90.00 + 85.00 = 175.00
    q = quote_for(
        [Line("A", 10), Line("B", 50)],
        [general("A", "10.00"), general("B", "2.00")],
    )
    assert q.subtotal == D("175.00")
    assert q.applied == ("volume:A", "volume:B")


@pytest.mark.ac("S2-AC1", "S2-AC3")
def test_applied_lists_volume_products_in_order_of_first_appearance():
    # Merged: B = 5 + 5 = 10 (first seen first), A = 10.
    # B: 10 x 10.00 = 100.00; 10% off -> 90.00
    # A: 10 x 10.00 = 100.00; 10% off -> 90.00
    # subtotal: 90.00 + 90.00 = 180.00
    # applied order follows first appearance: B, then A
    q = quote_for(
        [Line("B", 5), Line("A", 10), Line("B", 5)],
        [general("A", "10.00"), general("B", "10.00")],
    )
    assert q.subtotal == D("180.00")
    assert q.applied == ("volume:B", "volume:A")
