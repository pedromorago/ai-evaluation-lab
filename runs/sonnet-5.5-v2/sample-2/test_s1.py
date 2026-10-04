from datetime import date
from decimal import Decimal

import pytest

from checkout import (
    CartError,
    Coupon,
    Customer,
    Line,
    Product,
    price_cart,
)

TODAY = date(2026, 1, 15)


def D(value: str) -> Decimal:
    return Decimal(value)


def catalog() -> dict:
    return {
        "PEN": Product("PEN", "Pen", D("2.50")),
        "MUG": Product("MUG", "Mug", D("10.00")),
        "BK-1": Product("BK-1", "Book", D("1.00"), category="books"),
        "BK-2": Product("BK-2", "Other book", D("1.00"), category="books"),
    }


# ---------------------------------------------------------------- S1-AC1

@pytest.mark.ac("S1-AC1")
def test_single_line_costs_unit_price_times_quantity():
    quote = price_cart([Line("PEN", 3)], catalog(), today=TODAY)
    # 2.50 * 3 = 7.50
    assert quote.subtotal == D("7.50")


@pytest.mark.ac("S1-AC1")
def test_quantity_one_costs_exactly_the_unit_price():
    quote = price_cart([Line("MUG", 1)], catalog(), today=TODAY)
    # 10.00 * 1 = 10.00
    assert quote.subtotal == D("10.00")


@pytest.mark.ac("S1-AC1")
def test_subtotal_is_sum_of_line_totals_for_different_products():
    quote = price_cart([Line("PEN", 3), Line("MUG", 2)], catalog(), today=TODAY)
    # PEN: 2.50 * 3 = 7.50
    # MUG: 10.00 * 2 = 20.00
    # subtotal = 7.50 + 20.00 = 27.50
    assert quote.subtotal == D("27.50")


@pytest.mark.ac("S1-AC1")
def test_line_order_does_not_change_subtotal():
    quote = price_cart([Line("MUG", 2), Line("PEN", 3)], catalog(), today=TODAY)
    # 20.00 + 7.50 = 27.50
    assert quote.subtotal == D("27.50")


@pytest.mark.ac("S1-AC1")
def test_subtotal_reflects_volume_discount_on_the_line():
    quote = price_cart([Line("MUG", 10)], catalog(), today=TODAY)
    # 10.00 * 10 = 100.00, volume 10% off the line (S2-AC1): 100.00 - 10.00 = 90.00
    assert quote.subtotal == D("90.00")


# ---------------------------------------------------------------- S1-AC2

@pytest.mark.ac("S1-AC2")
@pytest.mark.parametrize("quantity", [0, -1, -50, 100, 101, 1000])
def test_quantity_outside_1_to_99_raises_cart_error(quantity):
    with pytest.raises(CartError):
        price_cart([Line("BK-1", quantity)], catalog(), today=TODAY)


@pytest.mark.ac("S1-AC2")
@pytest.mark.parametrize("quantity", [0.5, 1.5, 2.25, 98.5])
def test_fractional_quantity_raises_cart_error(quantity):
    with pytest.raises(CartError):
        price_cart([Line("BK-1", quantity)], catalog(), today=TODAY)


@pytest.mark.ac("S1-AC2")
def test_boolean_quantity_raises_cart_error():
    with pytest.raises(CartError):
        price_cart([Line("BK-1", True)], catalog(), today=TODAY)


@pytest.mark.ac("S1-AC2")
def test_boolean_false_quantity_raises_cart_error():
    with pytest.raises(CartError):
        price_cart([Line("BK-1", False)], catalog(), today=TODAY)


@pytest.mark.ac("S1-AC2")
def test_lowest_valid_quantity_1_is_accepted():
    quote = price_cart([Line("BK-1", 1)], catalog(), today=TODAY)
    # books: no volume discount. 1.00 * 1 = 1.00
    assert quote.subtotal == D("1.00")


@pytest.mark.ac("S1-AC2")
def test_highest_valid_quantity_99_is_accepted():
    quote = price_cart([Line("BK-1", 99)], catalog(), today=TODAY)
    # books: no volume discount. 1.00 * 99 = 99.00
    assert quote.subtotal == D("99.00")


@pytest.mark.ac("S1-AC2")
def test_one_invalid_line_among_valid_lines_raises_cart_error():
    with pytest.raises(CartError):
        price_cart([Line("PEN", 2), Line("MUG", 0)], catalog(), today=TODAY)


# ---------------------------------------------------------------- S1-AC3

@pytest.mark.ac("S1-AC3")
def test_unknown_sku_raises_cart_error():
    with pytest.raises(CartError):
        price_cart([Line("NOPE", 1)], catalog(), today=TODAY)


@pytest.mark.ac("S1-AC3")
def test_unknown_sku_among_known_skus_raises_cart_error():
    with pytest.raises(CartError):
        price_cart([Line("PEN", 1), Line("NOPE", 1)], catalog(), today=TODAY)


@pytest.mark.ac("S1-AC3")
def test_any_sku_raises_cart_error_with_empty_catalog():
    with pytest.raises(CartError):
        price_cart([Line("PEN", 1)], {}, today=TODAY)


# ---------------------------------------------------------------- S1-AC4

@pytest.mark.ac("S1-AC4")
def test_lines_with_same_sku_are_merged_and_quantities_added():
    quote = price_cart([Line("PEN", 3), Line("PEN", 4)], catalog(), today=TODAY)
    # merged PEN quantity 3 + 4 = 7; 2.50 * 7 = 17.50
    assert quote.subtotal == D("17.50")


@pytest.mark.ac("S1-AC4")
def test_merging_does_not_mix_different_skus():
    quote = price_cart(
        [Line("PEN", 2), Line("MUG", 1), Line("PEN", 1)], catalog(), today=TODAY
    )
    # PEN merged: 2 + 1 = 3 -> 2.50 * 3 = 7.50
    # MUG: 10.00 * 1 = 10.00
    # subtotal = 17.50
    assert quote.subtotal == D("17.50")


@pytest.mark.ac("S1-AC4")
def test_merged_quantity_of_exactly_99_is_accepted():
    quote = price_cart([Line("BK-1", 50), Line("BK-1", 49)], catalog(), today=TODAY)
    # merged 50 + 49 = 99 (books, no volume discount): 1.00 * 99 = 99.00
    assert quote.subtotal == D("99.00")


@pytest.mark.ac("S1-AC4")
def test_merged_quantity_of_100_raises_cart_error():
    with pytest.raises(CartError):
        price_cart([Line("BK-1", 50), Line("BK-1", 50)], catalog(), today=TODAY)


@pytest.mark.ac("S1-AC4")
def test_merged_quantity_above_100_raises_cart_error():
    with pytest.raises(CartError):
        price_cart([Line("BK-1", 99), Line("BK-1", 99)], catalog(), today=TODAY)


@pytest.mark.ac("S1-AC4")
def test_three_lines_merging_to_100_raise_cart_error():
    with pytest.raises(CartError):
        price_cart(
            [Line("BK-1", 33), Line("BK-1", 33), Line("BK-1", 34)],
            catalog(),
            today=TODAY,
        )


@pytest.mark.ac("S1-AC4")
def test_three_lines_merging_to_99_are_accepted():
    quote = price_cart(
        [Line("BK-1", 33), Line("BK-1", 33), Line("BK-1", 33)],
        catalog(),
        today=TODAY,
    )
    # merged 33 * 3 = 99; 1.00 * 99 = 99.00
    assert quote.subtotal == D("99.00")


@pytest.mark.ac("S1-AC4")
def test_different_skus_each_at_99_are_not_merged_together():
    quote = price_cart([Line("BK-1", 99), Line("BK-2", 99)], catalog(), today=TODAY)
    # BK-1: 1.00 * 99 = 99.00; BK-2: 1.00 * 99 = 99.00; subtotal = 198.00
    assert quote.subtotal == D("198.00")


@pytest.mark.ac("S1-AC4")
def test_merged_quantity_is_used_for_volume_discount():
    quote = price_cart([Line("MUG", 5), Line("MUG", 5)], catalog(), today=TODAY)
    # merged MUG quantity 5 + 5 = 10 -> volume 10% off (S2-AC1)
    # 10.00 * 10 = 100.00; 100.00 - 10.00 = 90.00
    assert quote.subtotal == D("90.00")


# ---------------------------------------------------------------- S1-AC5

@pytest.mark.ac("S1-AC5")
def test_empty_cart_quote_is_all_zero_and_nothing_applied():
    quote = price_cart([], catalog(), today=TODAY)
    assert quote.subtotal == D("0.00")
    assert quote.discount == D("0.00")
    assert quote.shipping == D("0.00")
    assert quote.tax == D("0.00")
    assert quote.total == D("0.00")
    assert quote.applied == ()


@pytest.mark.ac("S1-AC5")
def test_empty_cart_charges_no_express_shipping():
    quote = price_cart([], catalog(), today=TODAY, shipping="express")
    assert quote.shipping == D("0.00")
    assert quote.tax == D("0.00")
    assert quote.total == D("0.00")


@pytest.mark.ac("S1-AC5")
def test_empty_cart_ignores_gold_tier():
    quote = price_cart([], catalog(), today=TODAY, customer=Customer(tier="gold"))
    assert quote.subtotal == D("0.00")
    assert quote.discount == D("0.00")
    assert quote.total == D("0.00")
    assert quote.applied == ()


@pytest.mark.ac("S1-AC5")
def test_empty_cart_ignores_percent_coupon():
    coupon = Coupon(code="SAVE10", kind="percent", value=D("10"))
    quote = price_cart([], catalog(), today=TODAY, coupon=coupon)
    assert quote.discount == D("0.00")
    assert quote.total == D("0.00")
    assert quote.applied == ()


@pytest.mark.ac("S1-AC5")
def test_empty_cart_ignores_fixed_coupon():
    coupon = Coupon(code="FIVE", kind="fixed", value=D("5.00"))
    quote = price_cart([], catalog(), today=TODAY, coupon=coupon)
    assert quote.subtotal == D("0.00")
    assert quote.discount == D("0.00")
    assert quote.shipping == D("0.00")
    assert quote.tax == D("0.00")
    assert quote.total == D("0.00")
    assert quote.applied == ()


@pytest.mark.ac("S1-AC5")
def test_empty_cart_ignores_coupon_that_would_otherwise_be_rejected():
    coupon = Coupon(
        code="OLD",
        kind="percent",
        value=D("10"),
        min_subtotal=D("100.00"),
        expires=date(2025, 1, 1),
    )
    quote = price_cart([], catalog(), today=TODAY, coupon=coupon)
    assert quote.total == D("0.00")
    assert quote.applied == ()


@pytest.mark.ac("S1-AC5")
def test_empty_cart_with_everything_set_is_still_zero():
    coupon = Coupon(code="SAVE10", kind="percent", value=D("10"))
    quote = price_cart(
        [],
        catalog(),
        today=TODAY,
        customer=Customer(tier="gold"),
        coupon=coupon,
        shipping="express",
    )
    assert quote.subtotal == D("0.00")
    assert quote.discount == D("0.00")
    assert quote.shipping == D("0.00")
    assert quote.tax == D("0.00")
    assert quote.total == D("0.00")
    assert quote.applied == ()
