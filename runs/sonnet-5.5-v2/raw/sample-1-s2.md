```python
from datetime import date
from decimal import Decimal

import pytest

from checkout import Customer, Line, Product, Quote, price_cart

TODAY = date(2026, 1, 15)


def D(value: str) -> Decimal:
    return Decimal(value)


def general(sku: str, price: str) -> Product:
    return Product(sku=sku, name=f"Product {sku}", unit_price=D(price))


def book(sku: str, price: str) -> Product:
    return Product(sku=sku, name=f"Book {sku}", unit_price=D(price), category="books")


def quote(lines, products):
    catalog = {p.sku: p for p in products}
    return price_cart(lines, catalog, today=TODAY)


# ---------------------------------------------------------------- S2-AC1


@pytest.mark.ac("S2-AC1")
def test_nine_units_get_no_volume_discount():
    # 9 x 2.00 = 18.00; below the 10-unit threshold, no discount.
    q = quote([Line("A", 9)], [general("A", "2.00")])
    assert q.subtotal == D("18.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC1")
def test_ten_units_get_ten_percent_off():
    # 10 x 2.00 = 20.00; 10% off -> 20.00 * 0.90 = 18.00.
    q = quote([Line("A", 10)], [general("A", "2.00")])
    assert q.subtotal == D("18.00")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC1")
def test_eleven_units_get_ten_percent_off():
    # 11 x 2.00 = 22.00; 10% off -> 22.00 * 0.90 = 19.80.
    q = quote([Line("A", 11)], [general("A", "2.00")])
    assert q.subtotal == D("19.80")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC1", "S2-AC2")
def test_forty_nine_units_still_get_ten_percent_not_fifteen():
    # 49 x 1.00 = 49.00; 10% off -> 49.00 * 0.90 = 44.10.
    q = quote([Line("A", 49)], [general("A", "1.00")])
    assert q.subtotal == D("44.10")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC1")
def test_volume_discount_uses_merged_quantity_of_duplicate_lines():
    # Lines 6 + 4 merge to 10 units; 10 x 1.00 = 10.00; 10% off -> 9.00.
    q = quote([Line("A", 6), Line("A", 4)], [general("A", "1.00")])
    assert q.subtotal == D("9.00")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC1")
def test_split_lines_below_threshold_after_merge_get_no_discount():
    # Lines 6 + 3 merge to 9 units; 9 x 1.00 = 9.00; no discount.
    q = quote([Line("A", 6), Line("A", 3)], [general("A", "1.00")])
    assert q.subtotal == D("9.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC1")
def test_volume_discount_applies_only_to_the_qualifying_line():
    # A: 10 x 3.00 = 30.00, 10% off -> 27.00.
    # B: 2 x 5.00 = 10.00, no discount.
    # Subtotal = 27.00 + 10.00 = 37.00.
    q = quote(
        [Line("A", 10), Line("B", 2)],
        [general("A", "3.00"), general("B", "5.00")],
    )
    assert q.subtotal == D("37.00")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC1")
def test_quantities_of_different_products_are_not_pooled():
    # 5 of A + 5 of B = 10 units overall, but only 5 of each: no discount.
    # A: 5 x 2.00 = 10.00; B: 5 x 2.00 = 10.00; subtotal 20.00.
    q = quote(
        [Line("A", 5), Line("B", 5)],
        [general("A", "2.00"), general("B", "2.00")],
    )
    assert q.subtotal == D("20.00")
    assert q.applied == ()


# ---------------------------------------------------------------- S2-AC2


@pytest.mark.ac("S2-AC2")
def test_fifty_units_get_fifteen_percent_off_instead_of_ten():
    # 50 x 1.00 = 50.00; 15% off -> 50.00 * 0.85 = 42.50.
    q = quote([Line("A", 50)], [general("A", "1.00")])
    assert q.subtotal == D("42.50")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC2")
def test_fifty_one_units_get_fifteen_percent_off():
    # 51 x 1.00 = 51.00; 15% off -> 51.00 * 0.85 = 43.35.
    q = quote([Line("A", 51)], [general("A", "1.00")])
    assert q.subtotal == D("43.35")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC2")
def test_ninety_nine_units_get_fifteen_percent_off():
    # 99 x 1.00 = 99.00; 15% off -> 99.00 * 0.85 = 84.15.
    q = quote([Line("A", 99)], [general("A", "1.00")])
    assert q.subtotal == D("84.15")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC2")
def test_fifteen_percent_tier_uses_merged_quantity_of_duplicate_lines():
    # Lines 30 + 20 merge to 50 units; 50 x 1.00 = 50.00; 15% off -> 42.50.
    q = quote([Line("A", 30), Line("A", 20)], [general("A", "1.00")])
    assert q.subtotal == D("42.50")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC2")
def test_merged_forty_nine_units_stay_in_ten_percent_tier():
    # Lines 30 + 19 merge to 49 units; 49 x 1.00 = 49.00; 10% off -> 44.10.
    q = quote([Line("A", 30), Line("A", 19)], [general("A", "1.00")])
    assert q.subtotal == D("44.10")
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S2-AC2")
def test_each_product_gets_its_own_tier():
    # A: 50 x 1.00 = 50.00, 15% off -> 42.50.
    # B: 10 x 2.00 = 20.00, 10% off -> 18.00.
    # Subtotal = 42.50 + 18.00 = 60.50.
    q = quote(
        [Line("A", 50), Line("B", 10)],
        [general("A", "1.00"), general("B", "2.00")],
    )
    assert q.subtotal == D("60.50")
    assert q.applied == ("volume:A", "volume:B")


# ---------------------------------------------------------------- S2-AC3


@pytest.mark.ac("S2-AC3")
def test_books_get_no_discount_at_ten_units():
    # 10 x 2.00 = 20.00; books never get a volume discount.
    q = quote([Line("BK", 10)], [book("BK", "2.00")])
    assert q.subtotal == D("20.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC3")
def test_books_get_no_discount_at_fifty_units():
    # 50 x 1.00 = 50.00; no discount.
    q = quote([Line("BK", 50)], [book("BK", "1.00")])
    assert q.subtotal == D("50.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC3")
def test_books_get_no_discount_at_ninety_nine_units():
    # 99 x 1.00 = 99.00; no discount.
    q = quote([Line("BK", 99)], [book("BK", "1.00")])
    assert q.subtotal == D("99.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC3")
def test_merged_book_lines_get_no_discount():
    # Lines 6 + 4 merge to 10 books; 10 x 2.00 = 20.00; no discount.
    q = quote([Line("BK", 6), Line("BK", 4)], [book("BK", "2.00")])
    assert q.subtotal == D("20.00")
    assert q.applied == ()


@pytest.mark.ac("S2-AC3", "S2-AC1")
def test_books_in_cart_do_not_stop_discount_on_other_products():
    # BK: 10 x 2.00 = 20.00, no discount.
    # A: 10 x 1.00 = 10.00, 10% off -> 9.00.
    # Subtotal = 20.00 + 9.00 = 29.00.
    q = quote(
        [Line("BK", 10), Line("A", 10)],
        [book("BK", "2.00"), general("A", "1.00")],
    )
    assert q.subtotal == D("29.00")
    assert q.applied == ("volume:A",)


# ------------------------------------------------- ordering and the quote


@pytest.mark.ac("S2-AC1", "S6-AC3")
def test_volume_entries_follow_first_appearance_order_in_cart():
    # B: 10 x 1.00 = 10.00 -> 9.00; A: 10 x 1.00 = 10.00 -> 9.00;
    # C: 1 x 1.00 = 1.00, no discount. Subtotal = 9.00 + 9.00 + 1.00 = 19.00.
    q = quote(
        [Line("B", 10), Line("A", 10), Line("C", 1)],
        [general("A", "1.00"), general("B", "1.00"), general("C", "1.00")],
    )
    assert q.subtotal == D("19.00")
    assert q.applied == ("volume:B", "volume:A")


@pytest.mark.ac("S2-AC1", "S1-AC4", "S6-AC3")
def test_volume_order_uses_first_appearance_of_merged_product():
    # Lines A(1), B(10), A(9): A merges to 10 and first appears before B.
    # A: 10 x 1.00 = 10.00 -> 9.00; B: 10 x 1.00 = 10.00 -> 9.00.
    # Subtotal = 18.00.
    q = quote(
        [Line("A", 1), Line("B", 10), Line("A", 9)],
        [general("A", "1.00"), general("B", "1.00")],
    )
    assert q.subtotal == D("18.00")
    assert q.applied == ("volume:A", "volume:B")


@pytest.mark.ac("S2-AC2", "S6-AC2")
def test_discounted_subtotal_is_rounded_half_up_to_the_cent():
    # 50 x 0.01 = 0.50; 15% off -> 0.50 * 0.85 = 0.425 -> rounded half up 0.43.
    q = quote([Line("A", 50)], [general("A", "0.01")])
    assert q.subtotal == D("0.43")


@pytest.mark.ac("S2-AC1", "S6-AC2")
def test_ten_percent_discounted_subtotal_is_rounded_half_up_to_the_cent():
    # 10 x 0.05 = 0.50; 10% off -> 0.50 * 0.90 = 0.45 (exact).
    q = quote([Line("A", 10)], [general("A", "0.05")])
    assert q.subtotal == D("0.45")


@pytest.mark.ac("S2-AC1", "S1-AC1", "S5-AC1", "S6-AC1", "S6-AC2")
def test_full_quote_with_volume_discount_and_paid_shipping():
    # 10 x 1.00 = 10.00; 10% off -> subtotal 9.00.
    # No coupon or loyalty -> discount 0.00.
    # Goods 9.00 < 50.00 -> standard shipping 4.99.
    # Tax = 21% of (9.00 + 4.99) = 0.21 * 13.99 = 2.9379 -> 2.94.
    # Total = 9.00 - 0.00 + 4.99 + 2.94 = 16.93.
    q = quote([Line("A", 10)], [general("A", "1.00")])
    assert q == Quote(
        subtotal=D("9.00"),
        discount=D("0.00"),
        shipping=D("4.99"),
        tax=D("2.94"),
        total=D("16.93"),
        applied=("volume:A",),
    )


@pytest.mark.ac("S2-AC1", "S5-AC1", "S6-AC1")
def test_full_quote_with_volume_discount_and_free_shipping():
    # 10 x 10.00 = 100.00; 10% off -> subtotal 90.00.
    # Discount 0.00; goods 90.00 >= 50.00 -> shipping 0.00.
    # Tax = 21% of 90.00 = 18.90.
    # Total = 90.00 - 0.00 + 0.00 + 18.90 = 108.90.
    q = quote([Line("A", 10)], [general("A", "10.00")])
    assert q == Quote(
        subtotal=D("90.00"),
        discount=D("0.00"),
        shipping=D("0.00"),
        tax=D("18.90"),
        total=D("108.90"),
        applied=("volume:A",),
    )


@pytest.mark.ac("S2-AC1", "S5-AC1")
def test_volume_discount_can_push_goods_below_free_shipping_threshold():
    # 10 x 5.50 = 55.00 before discount; 10% off -> 49.50 (< 50.00).
    # Standard shipping is therefore charged: 4.99.
    q = quote([Line("A", 10)], [general("A", "5.50")])
    assert q.subtotal == D("49.50")
    assert q.shipping == D("4.99")


@pytest.mark.ac("S2-AC1", "S4-AC1", "S6-AC2")
def test_loyalty_discount_is_computed_on_volume_discounted_subtotal():
    # 10 x 10.00 = 100.00; 10% off -> subtotal 90.00.
    # Gold: 5% of 90.00 = 4.50 discount.
    # Applied: volume first, then loyalty.
    catalog = {"A": general("A", "10.00")}
    q = price_cart(
        [Line("A", 10)],
        catalog,
        today=TODAY,
        customer=Customer(tier="gold"),
    )
    assert q.subtotal == D("90.00")
    assert q.discount == D("4.50")
    assert q.applied == ("volume:A", "loyalty")
```