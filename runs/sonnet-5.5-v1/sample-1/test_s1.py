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

TODAY = date(2030, 1, 15)

CATALOG = {
    "GEN-1": Product(sku="GEN-1", name="Widget", unit_price=Decimal("10.00")),
    "GEN-2": Product(sku="GEN-2", name="Gadget", unit_price=Decimal("2.50")),
    # Books never get a volume discount, so large quantities stay predictable.
    "BK-1": Product(
        sku="BK-1", name="Novel", unit_price=Decimal("1.00"), category="books"
    ),
}

ZERO = Decimal("0.00")


def price(lines, **kwargs):
    return price_cart(lines, CATALOG, today=TODAY, **kwargs)


# ---------------------------------------------------------------- S1-AC1


@pytest.mark.ac("S1-AC1")
def test_single_line_is_unit_price_times_quantity():
    quote = price([Line("GEN-2", 3)])
    assert quote.subtotal == Decimal("7.50")


@pytest.mark.ac("S1-AC1")
def test_quantity_one_costs_the_unit_price():
    quote = price([Line("GEN-1", 1)])
    assert quote.subtotal == Decimal("10.00")


@pytest.mark.ac("S1-AC1")
def test_subtotal_is_sum_of_line_totals():
    quote = price([Line("GEN-1", 2), Line("GEN-2", 3)])
    assert quote.subtotal == Decimal("27.50")


@pytest.mark.ac("S1-AC1")
def test_subtotal_sums_different_products_including_books():
    quote = price([Line("GEN-1", 1), Line("BK-1", 5), Line("GEN-2", 2)])
    assert quote.subtotal == Decimal("20.00")


@pytest.mark.ac("S1-AC1", "S2-AC1")
def test_subtotal_is_after_volume_discount():
    quote = price([Line("GEN-1", 10)])
    assert quote.subtotal == Decimal("90.00")


# ---------------------------------------------------------------- S1-AC2


@pytest.mark.ac("S1-AC2")
@pytest.mark.parametrize("quantity", [0, -1, -10, 100, 101, 1000])
def test_out_of_range_integer_quantity_is_rejected(quantity):
    with pytest.raises(CartError):
        price([Line("BK-1", quantity)])


@pytest.mark.ac("S1-AC2")
@pytest.mark.parametrize("quantity", [1.5, 0.5, 2.25, 99.5])
def test_fractional_quantity_is_rejected(quantity):
    with pytest.raises(CartError):
        price([Line("BK-1", quantity)])


@pytest.mark.ac("S1-AC2")
@pytest.mark.parametrize("quantity", [True, False])
def test_boolean_quantity_is_rejected(quantity):
    with pytest.raises(CartError):
        price([Line("BK-1", quantity)])


@pytest.mark.ac("S1-AC2")
def test_invalid_quantity_among_valid_lines_is_rejected():
    with pytest.raises(CartError):
        price([Line("GEN-1", 2), Line("GEN-2", 0)])


@pytest.mark.ac("S1-AC2")
def test_lower_boundary_quantity_one_is_accepted():
    quote = price([Line("BK-1", 1)])
    assert quote.subtotal == Decimal("1.00")


@pytest.mark.ac("S1-AC2")
def test_upper_boundary_quantity_99_is_accepted():
    quote = price([Line("BK-1", 99)])
    assert quote.subtotal == Decimal("99.00")


# ---------------------------------------------------------------- S1-AC3


@pytest.mark.ac("S1-AC3")
def test_unknown_sku_is_rejected():
    with pytest.raises(CartError):
        price([Line("NOPE", 1)])


@pytest.mark.ac("S1-AC3")
def test_unknown_sku_among_known_ones_is_rejected():
    with pytest.raises(CartError):
        price([Line("GEN-1", 1), Line("NOPE", 1), Line("GEN-2", 1)])


@pytest.mark.ac("S1-AC3")
def test_sku_lookup_is_exact():
    with pytest.raises(CartError):
        price([Line("gen-1", 1)])


# ---------------------------------------------------------------- S1-AC4


@pytest.mark.ac("S1-AC4")
def test_lines_with_same_sku_are_merged():
    merged = price([Line("GEN-2", 2), Line("GEN-2", 3)])
    single = price([Line("GEN-2", 5)])
    assert merged.subtotal == Decimal("12.50")
    assert merged == single


@pytest.mark.ac("S1-AC4")
def test_merging_keeps_other_lines_separate():
    quote = price([Line("GEN-2", 1), Line("GEN-1", 1), Line("GEN-2", 1)])
    assert quote.subtotal == Decimal("15.00")


@pytest.mark.ac("S1-AC4", "S2-AC1")
def test_merged_quantity_counts_towards_volume_discount():
    quote = price([Line("GEN-1", 5), Line("GEN-1", 5)])
    assert quote.subtotal == Decimal("90.00")


@pytest.mark.ac("S1-AC4")
def test_merged_quantity_of_exactly_99_is_accepted():
    quote = price([Line("BK-1", 50), Line("BK-1", 49)])
    assert quote.subtotal == Decimal("99.00")


@pytest.mark.ac("S1-AC4")
@pytest.mark.parametrize(
    "quantities", [(50, 50), (99, 1), (1, 99), (60, 30, 10), (99, 99)]
)
def test_merged_quantity_above_99_is_rejected(quantities):
    lines = [Line("BK-1", q) for q in quantities]
    with pytest.raises(CartError):
        price(lines)


@pytest.mark.ac("S1-AC4")
def test_same_total_quantity_across_different_skus_is_fine():
    quote = price([Line("BK-1", 99), Line("GEN-2", 1)])
    assert quote.subtotal == Decimal("101.50")


# ---------------------------------------------------------------- S1-AC5


def assert_empty_quote(quote):
    assert quote.subtotal == ZERO
    assert quote.discount == ZERO
    assert quote.shipping == ZERO
    assert quote.tax == ZERO
    assert quote.total == ZERO
    assert tuple(quote.applied) == ()


@pytest.mark.ac("S1-AC5")
def test_empty_cart_costs_nothing():
    assert_empty_quote(price([]))


@pytest.mark.ac("S1-AC5")
def test_empty_cart_charges_no_express_shipping():
    assert_empty_quote(price([], shipping="express"))


@pytest.mark.ac("S1-AC5")
def test_empty_cart_ignores_loyalty_tier():
    assert_empty_quote(price([], customer=Customer(tier="gold")))


@pytest.mark.ac("S1-AC5")
@pytest.mark.parametrize(
    "coupon",
    [
        Coupon(code="SAVE10", kind="percent", value=Decimal("10")),
        Coupon(code="FIVE", kind="fixed", value=Decimal("5.00")),
    ],
)
def test_empty_cart_ignores_coupon(coupon):
    assert_empty_quote(price([], coupon=coupon))


@pytest.mark.ac("S1-AC5")
def test_empty_cart_ignores_coupon_that_would_not_apply():
    coupon = Coupon(
        code="BIG",
        kind="percent",
        value=Decimal("10"),
        min_subtotal=Decimal("100.00"),
        expires=date(2020, 1, 1),
    )
    assert_empty_quote(price([], coupon=coupon))


@pytest.mark.ac("S1-AC5")
def test_empty_cart_with_gold_coupon_and_express_is_still_zero():
    coupon = Coupon(code="SAVE10", kind="percent", value=Decimal("10"))
    quote = price(
        [], customer=Customer(tier="gold"), coupon=coupon, shipping="express"
    )
    assert_empty_quote(quote)
