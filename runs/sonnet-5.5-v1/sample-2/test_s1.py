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

TODAY = date(2026, 6, 15)
ZERO = Decimal("0.00")

CATALOG = {
    "GEN-10": Product(sku="GEN-10", name="Widget", unit_price=Decimal("10.00")),
    "GEN-3": Product(sku="GEN-3", name="Gadget", unit_price=Decimal("3.50")),
    "BK-1": Product(
        sku="BK-1", name="Novel", unit_price=Decimal("1.00"), category="books"
    ),
}


def price(lines, **kwargs):
    return price_cart(lines, CATALOG, today=TODAY, **kwargs)


# ---------- S1-AC1: line total = unit price * quantity, summed ----------


@pytest.mark.ac("S1-AC1")
def test_single_line_subtotal_is_price_times_quantity():
    quote = price([Line("GEN-10", 3)])
    assert quote.subtotal == Decimal("30.00")


@pytest.mark.ac("S1-AC1")
def test_quantity_one_costs_unit_price():
    quote = price([Line("GEN-3", 1)])
    assert quote.subtotal == Decimal("3.50")


@pytest.mark.ac("S1-AC1")
def test_subtotal_sums_line_totals_of_different_products():
    quote = price([Line("GEN-10", 2), Line("GEN-3", 3), Line("BK-1", 4)])
    # 20.00 + 10.50 + 4.00
    assert quote.subtotal == Decimal("34.50")


@pytest.mark.ac("S1-AC1")
def test_no_discount_applied_for_plain_cart():
    quote = price([Line("GEN-10", 2), Line("GEN-3", 1)])
    assert quote.subtotal == Decimal("23.50")
    assert quote.discount == ZERO
    assert quote.applied == ()


@pytest.mark.ac("S1-AC1", "S2-AC1")
def test_subtotal_is_after_volume_discount():
    quote = price([Line("GEN-10", 10)])
    # 10 * 10.00 = 100.00, minus 10% volume discount
    assert quote.subtotal == Decimal("90.00")
    assert quote.applied == ("volume:GEN-10",)


@pytest.mark.ac("S1-AC1", "S2-AC1")
def test_volume_discount_only_reduces_the_discounted_line():
    quote = price([Line("GEN-10", 10), Line("GEN-3", 2)])
    # 90.00 + 7.00
    assert quote.subtotal == Decimal("97.00")


# ---------- S1-AC2: quantity must be a whole number 1..99 ----------


@pytest.mark.ac("S1-AC2")
@pytest.mark.parametrize("quantity", [0, -1, -50, 100, 101, 1000])
def test_out_of_range_integer_quantity_is_rejected(quantity):
    with pytest.raises(CartError):
        price([Line("GEN-10", quantity)])


@pytest.mark.ac("S1-AC2")
@pytest.mark.parametrize("quantity", [1.5, 0.5, 2.25, 99.5])
def test_fractional_quantity_is_rejected(quantity):
    with pytest.raises(CartError):
        price([Line("GEN-10", quantity)])


@pytest.mark.ac("S1-AC2")
def test_boolean_quantity_is_rejected():
    with pytest.raises(CartError):
        price([Line("GEN-10", True)])


@pytest.mark.ac("S1-AC2")
def test_minimum_quantity_one_is_accepted():
    quote = price([Line("BK-1", 1)])
    assert quote.subtotal == Decimal("1.00")


@pytest.mark.ac("S1-AC2")
def test_maximum_quantity_99_is_accepted():
    # books never get a volume discount, so the subtotal is plain price * qty
    quote = price([Line("BK-1", 99)])
    assert quote.subtotal == Decimal("99.00")


@pytest.mark.ac("S1-AC2")
def test_one_invalid_line_among_valid_ones_rejects_the_cart():
    with pytest.raises(CartError):
        price([Line("GEN-10", 2), Line("GEN-3", 0)])


# ---------- S1-AC3: unknown SKU ----------


@pytest.mark.ac("S1-AC3")
def test_unknown_sku_is_rejected():
    with pytest.raises(CartError):
        price([Line("NOPE", 1)])


@pytest.mark.ac("S1-AC3")
def test_unknown_sku_among_known_ones_is_rejected():
    with pytest.raises(CartError):
        price([Line("GEN-10", 1), Line("NOPE", 1), Line("GEN-3", 1)])


@pytest.mark.ac("S1-AC3")
def test_sku_lookup_is_against_the_given_catalog():
    small_catalog = {"GEN-10": CATALOG["GEN-10"]}
    with pytest.raises(CartError):
        price_cart([Line("GEN-3", 1)], small_catalog, today=TODAY)


# ---------- S1-AC4: merging lines with the same SKU ----------


@pytest.mark.ac("S1-AC4")
def test_lines_with_same_sku_are_added_up():
    quote = price([Line("GEN-10", 2), Line("GEN-10", 3)])
    assert quote.subtotal == Decimal("50.00")


@pytest.mark.ac("S1-AC4")
def test_merging_works_when_lines_are_not_adjacent():
    quote = price([Line("GEN-10", 1), Line("GEN-3", 2), Line("GEN-10", 2)])
    # 3 * 10.00 + 2 * 3.50
    assert quote.subtotal == Decimal("37.00")


@pytest.mark.ac("S1-AC4", "S2-AC1")
def test_merged_quantity_counts_for_volume_discount():
    quote = price([Line("GEN-10", 5), Line("GEN-10", 5)])
    # 10 units merged -> 10% off 100.00
    assert quote.subtotal == Decimal("90.00")
    assert quote.applied == ("volume:GEN-10",)


@pytest.mark.ac("S1-AC4")
def test_merged_quantity_of_exactly_99_is_accepted():
    quote = price([Line("BK-1", 50), Line("BK-1", 49)])
    assert quote.subtotal == Decimal("99.00")


@pytest.mark.ac("S1-AC4")
@pytest.mark.parametrize(
    "first, second", [(50, 50), (99, 1), (60, 40), (1, 99)]
)
def test_merged_quantity_over_99_is_rejected(first, second):
    with pytest.raises(CartError):
        price([Line("BK-1", first), Line("BK-1", second)])


@pytest.mark.ac("S1-AC4")
def test_merged_quantity_over_99_is_rejected_across_other_lines():
    with pytest.raises(CartError):
        price([Line("BK-1", 60), Line("GEN-10", 1), Line("BK-1", 40)])


# ---------- S1-AC5: empty cart ----------


@pytest.mark.ac("S1-AC5")
def test_empty_cart_costs_nothing():
    quote = price([])
    assert quote.subtotal == ZERO
    assert quote.discount == ZERO
    assert quote.shipping == ZERO
    assert quote.tax == ZERO
    assert quote.total == ZERO
    assert quote.applied == ()


@pytest.mark.ac("S1-AC5")
def test_empty_cart_has_no_shipping_even_when_express():
    quote = price([], shipping="express")
    assert quote.shipping == ZERO
    assert quote.tax == ZERO
    assert quote.total == ZERO


@pytest.mark.ac("S1-AC5")
def test_empty_cart_ignores_gold_tier():
    quote = price([], customer=Customer(tier="gold"))
    assert quote.subtotal == ZERO
    assert quote.discount == ZERO
    assert quote.total == ZERO
    assert quote.applied == ()


@pytest.mark.ac("S1-AC5")
@pytest.mark.parametrize(
    "coupon",
    [
        Coupon(code="SAVE10", kind="percent", value=Decimal("10")),
        Coupon(code="FIVE", kind="fixed", value=Decimal("5.00")),
    ],
)
def test_empty_cart_ignores_coupon(coupon):
    quote = price([], coupon=coupon)
    assert quote.subtotal == ZERO
    assert quote.discount == ZERO
    assert quote.shipping == ZERO
    assert quote.tax == ZERO
    assert quote.total == ZERO
    assert quote.applied == ()


@pytest.mark.ac("S1-AC5")
def test_empty_cart_does_not_validate_coupon_minimum_or_expiry():
    coupon = Coupon(
        code="BIG",
        kind="percent",
        value=Decimal("10"),
        min_subtotal=Decimal("100.00"),
        expires=date(2020, 1, 1),
    )
    quote = price([], coupon=coupon)
    assert quote.total == ZERO
    assert quote.applied == ()


@pytest.mark.ac("S1-AC5")
def test_empty_cart_with_gold_and_coupon_together():
    coupon = Coupon(code="SAVE10", kind="percent", value=Decimal("10"))
    quote = price(
        [], customer=Customer(tier="gold"), coupon=coupon, shipping="express"
    )
    assert quote.subtotal == ZERO
    assert quote.discount == ZERO
    assert quote.shipping == ZERO
    assert quote.tax == ZERO
    assert quote.total == ZERO
    assert quote.applied == ()
