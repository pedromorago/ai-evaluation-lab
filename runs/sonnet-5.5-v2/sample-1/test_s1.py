from datetime import date
from decimal import Decimal

import pytest

from checkout import (
    CartError,
    Coupon,
    Customer,
    Line,
    Product,
    Quote,
    price_cart,
)

TODAY = date(2026, 10, 3)
ZERO = Decimal("0.00")


def make_catalog():
    return {
        "G-1": Product("G-1", "Gadget", Decimal("10.00")),
        "G-2": Product("G-2", "Widget", Decimal("3.25")),
        "G-5": Product("G-5", "Fiver", Decimal("5.00")),
        "G-S": Product("G-S", "Small", Decimal("2.50")),
        "G-N": Product("G-N", "Nine", Decimal("1.11")),
        "BK-1": Product("BK-1", "Novel", Decimal("2.00"), category="books"),
    }


def subtotal_of(lines):
    return price_cart(lines, make_catalog(), today=TODAY).subtotal


# ---------------------------------------------------------------- S1-AC1

@pytest.mark.ac("S1-AC1")
def test_single_line_costs_unit_price_times_quantity():
    # 2.50 * 3 = 7.50
    assert subtotal_of([Line("G-S", 3)]) == Decimal("7.50")


@pytest.mark.ac("S1-AC1")
def test_quantity_one_costs_the_unit_price():
    # 10.00 * 1 = 10.00
    assert subtotal_of([Line("G-1", 1)]) == Decimal("10.00")


@pytest.mark.ac("S1-AC1")
def test_subtotal_is_sum_of_line_totals_for_different_skus():
    # G-1: 10.00 * 2 = 20.00
    # G-2: 3.25 * 4 = 13.00
    # subtotal = 20.00 + 13.00 = 33.00
    assert subtotal_of([Line("G-1", 2), Line("G-2", 4)]) == Decimal("33.00")


@pytest.mark.ac("S1-AC1")
def test_three_different_lines_are_all_summed():
    # G-1: 10.00 * 1 = 10.00
    # G-2: 3.25 * 2 = 6.50
    # G-S: 2.50 * 3 = 7.50
    # subtotal = 10.00 + 6.50 + 7.50 = 24.00
    lines = [Line("G-1", 1), Line("G-2", 2), Line("G-S", 3)]
    assert subtotal_of(lines) == Decimal("24.00")


@pytest.mark.ac("S1-AC1")
def test_nine_units_have_no_volume_discount_in_subtotal():
    # 9 units is below the 10-unit volume threshold:
    # 1.11 * 9 = 9.99
    assert subtotal_of([Line("G-N", 9)]) == Decimal("9.99")


@pytest.mark.ac("S1-AC1")
def test_subtotal_is_after_volume_discount():
    # G-5: 5.00 * 10 = 50.00; 10 units -> 10% off: 50.00 - 5.00 = 45.00
    assert subtotal_of([Line("G-5", 10)]) == Decimal("45.00")


@pytest.mark.ac("S1-AC1")
def test_subtotal_sums_discounted_and_undiscounted_lines():
    # G-5: 5.00 * 10 = 50.00, minus 10% = 45.00
    # G-1: 10.00 * 2 = 20.00 (no discount)
    # subtotal = 45.00 + 20.00 = 65.00
    assert subtotal_of([Line("G-5", 10), Line("G-1", 2)]) == Decimal("65.00")


@pytest.mark.ac("S1-AC1")
def test_quote_is_returned_with_decimal_subtotal():
    quote = price_cart([Line("G-S", 2)], make_catalog(), today=TODAY)
    assert isinstance(quote, Quote)
    # 2.50 * 2 = 5.00
    assert quote.subtotal == Decimal("5.00")
    assert isinstance(quote.subtotal, Decimal)


# ---------------------------------------------------------------- S1-AC2

@pytest.mark.ac("S1-AC2")
@pytest.mark.parametrize("quantity", [0, -1, -50, 100, 101, 1000])
def test_out_of_range_integer_quantity_raises_cart_error(quantity):
    with pytest.raises(CartError):
        price_cart([Line("BK-1", quantity)], make_catalog(), today=TODAY)


@pytest.mark.ac("S1-AC2")
@pytest.mark.parametrize("quantity", [1.5, 0.5, 2.25, 99.5])
def test_fractional_quantity_raises_cart_error(quantity):
    with pytest.raises(CartError):
        price_cart([Line("BK-1", quantity)], make_catalog(), today=TODAY)


@pytest.mark.ac("S1-AC2")
def test_boolean_true_quantity_raises_cart_error():
    with pytest.raises(CartError):
        price_cart([Line("BK-1", True)], make_catalog(), today=TODAY)


@pytest.mark.ac("S1-AC2")
def test_boolean_false_quantity_raises_cart_error():
    with pytest.raises(CartError):
        price_cart([Line("BK-1", False)], make_catalog(), today=TODAY)


@pytest.mark.ac("S1-AC2")
def test_minimum_quantity_one_is_accepted():
    # books 2.00 * 1 = 2.00
    assert subtotal_of([Line("BK-1", 1)]) == Decimal("2.00")


@pytest.mark.ac("S1-AC2")
def test_maximum_quantity_99_is_accepted():
    # books never get a volume discount: 2.00 * 99 = 198.00
    assert subtotal_of([Line("BK-1", 99)]) == Decimal("198.00")


@pytest.mark.ac("S1-AC2")
def test_quantity_100_is_rejected_just_above_the_limit():
    with pytest.raises(CartError):
        price_cart([Line("BK-1", 100)], make_catalog(), today=TODAY)


@pytest.mark.ac("S1-AC2")
def test_invalid_quantity_on_one_line_rejects_the_whole_cart():
    with pytest.raises(CartError):
        price_cart(
            [Line("G-1", 2), Line("G-2", 0)], make_catalog(), today=TODAY
        )


# ---------------------------------------------------------------- S1-AC3

@pytest.mark.ac("S1-AC3")
def test_unknown_sku_raises_cart_error():
    with pytest.raises(CartError):
        price_cart([Line("NOPE", 1)], make_catalog(), today=TODAY)


@pytest.mark.ac("S1-AC3")
def test_unknown_sku_among_valid_lines_raises_cart_error():
    with pytest.raises(CartError):
        price_cart(
            [Line("G-1", 1), Line("NOPE", 1), Line("G-2", 1)],
            make_catalog(),
            today=TODAY,
        )


@pytest.mark.ac("S1-AC3")
def test_any_sku_is_unknown_with_an_empty_catalog():
    with pytest.raises(CartError):
        price_cart([Line("G-1", 1)], {}, today=TODAY)


# ---------------------------------------------------------------- S1-AC4

@pytest.mark.ac("S1-AC4")
def test_lines_with_same_sku_are_merged_by_adding_quantities():
    # G-1: 2 + 3 = 5 units; 10.00 * 5 = 50.00
    assert subtotal_of([Line("G-1", 2), Line("G-1", 3)]) == Decimal("50.00")


@pytest.mark.ac("S1-AC4")
def test_merging_happens_alongside_other_skus():
    # G-1: 1 + 2 = 3 units -> 30.00
    # G-2: 3.25 * 2 = 6.50
    # subtotal = 30.00 + 6.50 = 36.50
    lines = [Line("G-1", 1), Line("G-2", 2), Line("G-1", 2)]
    assert subtotal_of(lines) == Decimal("36.50")


@pytest.mark.ac("S1-AC4")
def test_merged_quantity_is_what_decides_the_volume_discount():
    # G-5: 5 + 5 = 10 merged units; 5.00 * 10 = 50.00, 10% off = 45.00
    # (unmerged, neither 5-unit line would be discounted: 50.00 total)
    assert subtotal_of([Line("G-5", 5), Line("G-5", 5)]) == Decimal("45.00")


@pytest.mark.ac("S1-AC4")
def test_merged_quantity_of_exactly_99_is_accepted():
    # books: 60 + 39 = 99 units; 2.00 * 99 = 198.00
    assert subtotal_of([Line("BK-1", 60), Line("BK-1", 39)]) == Decimal("198.00")


@pytest.mark.ac("S1-AC4")
def test_merged_quantity_of_98_is_accepted():
    # books: 98 + ... via 97 + 1 = 98 units; 2.00 * 98 = 196.00
    assert subtotal_of([Line("BK-1", 97), Line("BK-1", 1)]) == Decimal("196.00")


@pytest.mark.ac("S1-AC4")
def test_merged_quantity_of_100_raises_cart_error():
    # each line is valid alone (50), but 50 + 50 = 100 > 99
    with pytest.raises(CartError):
        price_cart(
            [Line("BK-1", 50), Line("BK-1", 50)], make_catalog(), today=TODAY
        )


@pytest.mark.ac("S1-AC4")
def test_merged_quantity_of_101_raises_cart_error():
    with pytest.raises(CartError):
        price_cart(
            [Line("BK-1", 99), Line("BK-1", 2)], make_catalog(), today=TODAY
        )


@pytest.mark.ac("S1-AC4")
def test_merged_quantity_over_99_across_three_lines_raises_cart_error():
    # 40 + 40 + 20 = 100
    with pytest.raises(CartError):
        price_cart(
            [Line("BK-1", 40), Line("BK-1", 40), Line("BK-1", 20)],
            make_catalog(),
            today=TODAY,
        )


@pytest.mark.ac("S1-AC4", "S1-AC2")
def test_invalid_line_quantity_is_rejected_even_if_merge_would_be_valid():
    # the 0 is an invalid quantity on its own line
    with pytest.raises(CartError):
        price_cart(
            [Line("G-1", 0), Line("G-1", 5)], make_catalog(), today=TODAY
        )


# ---------------------------------------------------------------- S1-AC5

@pytest.mark.ac("S1-AC5")
def test_empty_cart_quote_is_all_zero_with_nothing_applied():
    quote = price_cart([], make_catalog(), today=TODAY)
    assert quote.subtotal == ZERO
    assert quote.discount == ZERO
    assert quote.shipping == ZERO
    assert quote.tax == ZERO
    assert quote.total == ZERO
    assert quote.applied == ()


@pytest.mark.ac("S1-AC5")
def test_empty_cart_has_no_standard_shipping_charge():
    quote = price_cart([], make_catalog(), today=TODAY, shipping="standard")
    assert quote.shipping == ZERO
    assert quote.total == ZERO


@pytest.mark.ac("S1-AC5")
def test_empty_cart_has_no_express_shipping_charge():
    quote = price_cart([], make_catalog(), today=TODAY, shipping="express")
    assert quote.shipping == ZERO
    assert quote.tax == ZERO
    assert quote.total == ZERO


@pytest.mark.ac("S1-AC5")
def test_empty_cart_ignores_percent_coupon():
    coupon = Coupon("SAVE10", "percent", Decimal("10"))
    quote = price_cart([], make_catalog(), today=TODAY, coupon=coupon)
    assert quote.discount == ZERO
    assert quote.total == ZERO
    assert quote.applied == ()


@pytest.mark.ac("S1-AC5")
def test_empty_cart_ignores_fixed_coupon():
    coupon = Coupon("FIVE", "fixed", Decimal("5.00"))
    quote = price_cart([], make_catalog(), today=TODAY, coupon=coupon)
    assert quote.discount == ZERO
    assert quote.total == ZERO
    assert quote.applied == ()


@pytest.mark.ac("S1-AC5")
def test_empty_cart_ignores_gold_loyalty_tier():
    quote = price_cart(
        [], make_catalog(), today=TODAY, customer=Customer(tier="gold")
    )
    assert quote.discount == ZERO
    assert quote.total == ZERO
    assert quote.applied == ()


@pytest.mark.ac("S1-AC5")
def test_empty_cart_ignores_coupon_loyalty_and_express_together():
    coupon = Coupon("SAVE10", "percent", Decimal("10"))
    quote = price_cart(
        [],
        make_catalog(),
        today=TODAY,
        customer=Customer(tier="gold"),
        coupon=coupon,
        shipping="express",
    )
    assert quote == Quote(
        subtotal=ZERO,
        discount=ZERO,
        shipping=ZERO,
        tax=ZERO,
        total=ZERO,
        applied=(),
    )
