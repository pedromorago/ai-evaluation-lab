from datetime import date
from decimal import Decimal

import pytest

from checkout import Coupon, Customer, Line, Product, price_cart

TODAY = date(2026, 10, 3)
CENT = Decimal("0.01")


def D(s):
    return Decimal(s)


def catalog(**prices):
    """Build a catalog from SKU=price keyword arguments (general category)."""
    return {sku: Product(sku, sku, D(price)) for sku, price in prices.items()}


def cents(x):
    return x == x.quantize(CENT)


# ---------------------------------------------------------------- S6-AC1


@pytest.mark.ac("S6-AC1")
def test_tax_is_21_percent_of_goods_plus_standard_shipping():
    q = price_cart([Line("A", 1)], catalog(A="10.00"), today=TODAY)
    assert q.shipping == D("4.99")
    assert q.tax == D("3.15")  # 0.21 * 14.99 = 3.1479
    assert q.total == D("18.14")


@pytest.mark.ac("S6-AC1")
def test_tax_includes_express_shipping():
    q = price_cart([Line("A", 1)], catalog(A="100.00"), today=TODAY, shipping="express")
    assert q.shipping == D("9.99")
    assert q.tax == D("23.10")  # 0.21 * 109.99 = 23.0979
    assert q.total == D("133.09")


@pytest.mark.ac("S6-AC1")
def test_tax_is_computed_after_loyalty_discount():
    q = price_cart(
        [Line("A", 1)], catalog(A="100.00"), today=TODAY, customer=Customer("gold")
    )
    assert q.subtotal == D("100.00")
    assert q.discount == D("5.00")
    assert q.shipping == D("0")
    assert q.tax == D("19.95")  # 0.21 * 95.00
    assert q.total == D("114.95")


@pytest.mark.ac("S6-AC1")
def test_tax_is_computed_after_percent_coupon():
    coupon = Coupon("SAVE10", "percent", D("10"))
    q = price_cart([Line("A", 1)], catalog(A="100.00"), today=TODAY, coupon=coupon)
    assert q.discount == D("10.00")
    assert q.tax == D("18.90")  # 0.21 * 90.00
    assert q.total == D("108.90")


@pytest.mark.ac("S6-AC1")
def test_tax_is_computed_after_fixed_coupon_and_includes_shipping():
    coupon = Coupon("FIX5", "fixed", D("5"))
    q = price_cart([Line("A", 1)], catalog(A="20.00"), today=TODAY, coupon=coupon)
    assert q.discount == D("5.00")
    assert q.shipping == D("4.99")
    assert q.tax == D("4.20")  # 0.21 * (15.00 + 4.99) = 4.1979
    assert q.total == D("20.19")


@pytest.mark.ac("S6-AC1")
def test_tax_is_computed_after_volume_discount():
    q = price_cart([Line("A", 10)], catalog(A="10.00"), today=TODAY)
    assert q.subtotal == D("90.00")
    assert q.tax == D("18.90")
    assert q.total == D("108.90")


# ---------------------------------------------------------------- S6-AC2


@pytest.mark.ac("S6-AC2")
def test_tax_rounds_half_up_not_half_even():
    # goods 0.51 + express 9.99 = 10.50 -> tax 2.205 -> 2.21 (half-even would give 2.20)
    q = price_cart([Line("A", 1)], catalog(A="0.51"), today=TODAY, shipping="express")
    assert q.tax == D("2.21")
    assert q.total == D("12.71")


@pytest.mark.ac("S6-AC2")
def test_loyalty_discount_rounds_half_up():
    # 5% of 0.10 = 0.005 -> 0.01 (half-even would give 0.00)
    q = price_cart(
        [Line("A", 1)], catalog(A="0.10"), today=TODAY, customer=Customer("gold")
    )
    assert q.subtotal == D("0.10")
    assert q.discount == D("0.01")
    assert q.tax == D("1.07")  # 0.21 * (0.09 + 4.99) = 1.0668
    assert q.total == D("6.15")


@pytest.mark.ac("S6-AC2")
def test_percent_coupon_discount_rounds_half_up():
    # 10% of 0.05 = 0.005 -> 0.01
    coupon = Coupon("SAVE10", "percent", D("10"))
    q = price_cart([Line("A", 1)], catalog(A="0.05"), today=TODAY, coupon=coupon)
    assert q.discount == D("0.01")
    assert q.tax == D("1.06")  # 0.21 * 5.03 = 1.0563
    assert q.total == D("6.09")


@pytest.mark.ac("S6-AC2")
def test_subtotal_rounds_half_up_after_volume_discount():
    # 50 * 0.01 = 0.50, minus 15% = 0.425 -> 0.43
    q = price_cart([Line("A", 50)], catalog(A="0.01"), today=TODAY)
    assert q.subtotal == D("0.43")
    assert q.tax == D("1.14")  # 0.21 * 5.42 = 1.1382
    assert q.total == D("6.56")


@pytest.mark.ac("S6-AC2")
def test_total_is_exact_sum_of_rounded_parts_with_fixed_and_loyalty():
    coupon = Coupon("FIX10", "fixed", D("10"))
    q = price_cart(
        [Line("A", 1)],
        catalog(A="100.00"),
        today=TODAY,
        customer=Customer("gold"),
        coupon=coupon,
    )
    assert q.subtotal == D("100.00")
    assert q.discount == D("15.00")
    assert q.shipping == D("0")
    assert q.tax == D("17.85")
    assert q.total == D("102.85")


@pytest.mark.ac("S6-AC2")
@pytest.mark.parametrize(
    "lines, prices, customer, coupon, shipping",
    [
        ([Line("A", 1)], {"A": "0.51"}, Customer(), None, "express"),
        ([Line("A", 3)], {"A": "3.33"}, Customer("gold"), None, "standard"),
        ([Line("A", 7)], {"A": "1.07"}, Customer(), Coupon("P", "percent", D("7")), "standard"),
        ([Line("A", 13)], {"A": "2.37"}, Customer("gold"), Coupon("F", "fixed", D("1.5")), "express"),
        ([Line("A", 50)], {"A": "0.33"}, Customer(), None, "standard"),
        ([Line("A", 4), Line("B", 11)], {"A": "9.99", "B": "0.77"}, Customer("gold"), None, "standard"),
    ],
)
def test_every_amount_is_in_cents_and_total_adds_up(lines, prices, customer, coupon, shipping):
    q = price_cart(
        lines,
        catalog(**prices),
        today=TODAY,
        customer=customer,
        coupon=coupon,
        shipping=shipping,
    )
    for amount in (q.subtotal, q.discount, q.shipping, q.tax, q.total):
        assert cents(amount)
    assert q.total == q.subtotal - q.discount + q.shipping + q.tax


# ---------------------------------------------------------------- S6-AC3


@pytest.mark.ac("S6-AC3")
def test_applied_is_empty_when_nothing_applies():
    q = price_cart([Line("A", 1)], catalog(A="10.00"), today=TODAY)
    assert q.applied == ()


@pytest.mark.ac("S6-AC3")
def test_applied_lists_volume_in_cart_order():
    q = price_cart(
        [Line("C", 50), Line("B", 1), Line("A", 10)],
        catalog(A="1.00", B="1.00", C="1.00"),
        today=TODAY,
    )
    assert q.applied == ("volume:C", "volume:A")


@pytest.mark.ac("S6-AC3")
def test_applied_volume_order_uses_first_appearance_after_merging():
    q = price_cart(
        [Line("A", 5), Line("C", 50), Line("A", 5)],
        catalog(A="1.00", C="1.00"),
        today=TODAY,
    )
    assert q.applied == ("volume:A", "volume:C")


@pytest.mark.ac("S6-AC3")
def test_applied_has_no_volume_entry_for_books():
    cat = {
        "BK-1": Product("BK-1", "Book", D("10.00"), category="books"),
        "A": Product("A", "A", D("1.00")),
    }
    q = price_cart([Line("BK-1", 20), Line("A", 10)], cat, today=TODAY)
    assert q.applied == ("volume:A",)


@pytest.mark.ac("S6-AC3")
def test_applied_loyalty_alone():
    q = price_cart(
        [Line("A", 1)], catalog(A="10.00"), today=TODAY, customer=Customer("gold")
    )
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S6-AC3")
def test_applied_percent_coupon_alone():
    coupon = Coupon("SAVE10", "percent", D("10"))
    q = price_cart([Line("A", 1)], catalog(A="10.00"), today=TODAY, coupon=coupon)
    assert q.applied == ("coupon:SAVE10",)


@pytest.mark.ac("S6-AC3")
def test_applied_loyalty_wins_over_smaller_percent_coupon():
    coupon = Coupon("SMALL", "percent", D("3"))
    q = price_cart(
        [Line("A", 1)],
        catalog(A="100.00"),
        today=TODAY,
        customer=Customer("gold"),
        coupon=coupon,
    )
    assert q.applied == ("loyalty",)


@pytest.mark.ac("S6-AC3")
def test_applied_coupon_wins_over_smaller_loyalty():
    coupon = Coupon("BIG", "percent", D("10"))
    q = price_cart(
        [Line("A", 1)],
        catalog(A="100.00"),
        today=TODAY,
        customer=Customer("gold"),
        coupon=coupon,
    )
    assert q.applied == ("coupon:BIG",)


@pytest.mark.ac("S6-AC3")
def test_applied_coupon_wins_when_equal_to_loyalty():
    coupon = Coupon("FIVE", "percent", D("5"))
    q = price_cart(
        [Line("A", 1)],
        catalog(A="100.00"),
        today=TODAY,
        customer=Customer("gold"),
        coupon=coupon,
    )
    assert q.applied == ("coupon:FIVE",)


@pytest.mark.ac("S6-AC3")
def test_applied_fixed_coupon_alone():
    coupon = Coupon("FIX5", "fixed", D("5"))
    q = price_cart([Line("A", 1)], catalog(A="20.00"), today=TODAY, coupon=coupon)
    assert q.applied == ("coupon:FIX5",)


@pytest.mark.ac("S6-AC3")
def test_applied_fixed_coupon_comes_after_loyalty():
    coupon = Coupon("FIX5", "fixed", D("5"))
    q = price_cart(
        [Line("A", 1)],
        catalog(A="100.00"),
        today=TODAY,
        customer=Customer("gold"),
        coupon=coupon,
    )
    assert q.applied == ("loyalty", "coupon:FIX5")


@pytest.mark.ac("S6-AC3")
def test_applied_full_order_volume_loyalty_fixed():
    coupon = Coupon("FIX5", "fixed", D("5"))
    q = price_cart(
        [Line("B", 10), Line("A", 50), Line("C", 1)],
        catalog(A="1.00", B="1.00", C="1.00"),
        today=TODAY,
        customer=Customer("gold"),
        coupon=coupon,
    )
    assert q.applied == ("volume:B", "volume:A", "loyalty", "coupon:FIX5")
