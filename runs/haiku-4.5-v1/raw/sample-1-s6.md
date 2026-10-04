```python
import pytest
from decimal import Decimal
from datetime import date
from checkout import (
    Product,
    Line,
    Customer,
    Coupon,
    price_cart,
)

TODAY = date(2026, 10, 3)


class TestS6AC1TaxCalculation:
    """S6-AC1: VAT is 21% of the goods after discounts plus shipping."""

    @pytest.mark.ac("S6-AC1")
    def test_tax_is_21_percent_of_goods_and_shipping(self):
        """Tax should be 21% of (goods after discounts + shipping)"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        quote = price_cart(lines, catalog, today=TODAY)

        # goods: 100.00, shipping: 4.99
        # tax: (100.00 + 4.99) * 0.21 = 22.0479 -> 22.05
        assert quote.tax == Decimal("22.05")

    @pytest.mark.ac("S6-AC1")
    def test_tax_with_volume_discount(self):
        """Tax calculated on goods after volume discount"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("10.00"))}
        lines = [Line("ITEM", 10)]  # 10% volume discount
        quote = price_cart(lines, catalog, today=TODAY)

        # subtotal: 100.00, volume discount: 10.00, goods: 90.00
        # shipping: 0.00 (free when goods >= 50.00)
        # tax: 90.00 * 0.21 = 18.90
        assert quote.tax == Decimal("18.90")

    @pytest.mark.ac("S6-AC1")
    def test_tax_with_percent_coupon(self):
        """Tax calculated on goods after percent coupon discount"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        coupon = Coupon("SAVE10", "percent", Decimal("10"))
        quote = price_cart(lines, catalog, today=TODAY, coupon=coupon)

        # goods after discount: 90.00, shipping: 0.00
        # tax: 90.00 * 0.21 = 18.90
        assert quote.tax == Decimal("18.90")

    @pytest.mark.ac("S6-AC1")
    def test_tax_with_loyalty_discount(self):
        """Tax calculated on goods after loyalty discount"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        customer = Customer(tier="gold")
        quote = price_cart(lines, catalog, today=TODAY, customer=customer)

        # goods after 5% loyalty: 95.00, shipping: 0.00
        # tax: 95.00 * 0.21 = 19.95
        assert quote.tax == Decimal("19.95")

    @pytest.mark.ac("S6-AC1")
    def test_tax_with_fixed_coupon(self):
        """Tax calculated on goods after fixed coupon discount"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        coupon = Coupon("MINUS10", "fixed", Decimal("10"))
        quote = price_cart(lines, catalog, today=TODAY, coupon=coupon)

        # goods after discount: 90.00, shipping: 0.00
        # tax: 90.00 * 0.21 = 18.90
        assert quote.tax == Decimal("18.90")

    @pytest.mark.ac("S6-AC1")
    def test_tax_with_express_shipping(self):
        """Tax includes express shipping cost"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        quote = price_cart(lines, catalog, today=TODAY, shipping="express")

        # goods: 100.00, shipping: 9.99
        # tax: (100.00 + 9.99) * 0.21 = 23.0979 -> 23.10
        assert quote.tax == Decimal("23.10")

    @pytest.mark.ac("S6-AC1")
    def test_tax_empty_cart(self):
        """Tax is zero on empty cart"""
        lines = []
        catalog = {}
        quote = price_cart(lines, catalog, today=TODAY)

        assert quote.tax == Decimal("0.00")


class TestS6AC2Rounding:
    """S6-AC2: Amounts rounded half up to cent; Total = subtotal − discount + shipping + tax."""

    @pytest.mark.ac("S6-AC2")
    def test_subtotal_rounded_half_up_down(self):
        """Subtotal rounded half up to the cent"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("33.334"))}
        lines = [Line("ITEM", 1)]
        quote = price_cart(lines, catalog, today=TODAY)

        # 33.334 -> 33.33
        assert quote.subtotal == Decimal("33.33")

    @pytest.mark.ac("S6-AC2")
    def test_subtotal_rounded_half_up_rounding_5(self):
        """Subtotal with .XX5 rounds up (half up rule)"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("33.335"))}
        lines = [Line("ITEM", 1)]
        quote = price_cart(lines, catalog, today=TODAY)

        # 33.335 -> 33.34
        assert quote.subtotal == Decimal("33.34")

    @pytest.mark.ac("S6-AC2")
    def test_discount_rounded_half_up(self):
        """Discount rounded half up to the cent"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        coupon = Coupon("SAVE33", "percent", Decimal("33"))
        quote = price_cart(lines, catalog, today=TODAY, coupon=coupon)

        # discount: 100.00 * 0.33 = 33.00
        assert quote.discount == Decimal("33.00")

    @pytest.mark.ac("S6-AC2")
    def test_volume_discount_rounded_half_up(self):
        """Volume discount rounded half up to the cent"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 10)]  # 10% volume discount
        quote = price_cart(lines, catalog, today=TODAY)

        # discount: 100.00 * 0.10 = 10.00
        assert quote.discount == Decimal("10.00")

    @pytest.mark.ac("S6-AC2")
    def test_tax_rounded_half_up_down(self):
        """Tax rounded half up to the cent"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        quote = price_cart(lines, catalog, today=TODAY)

        # tax: (100.00 + 4.99) * 0.21 = 22.0479 -> 22.05
        assert quote.tax == Decimal("22.05")

    @pytest.mark.ac("S6-AC2")
    def test_tax_rounded_half_up_rounding_5(self):
        """Tax with .XX5 rounds up (half up rule)"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("119.05"))}
        lines = [Line("ITEM", 1)]
        quote = price_cart(lines, catalog, today=TODAY)

        # goods: 119.05, shipping: 4.99
        # tax: (119.05 + 4.99) * 0.21 = 124.04 * 0.21 = 26.0484 -> 26.05
        assert quote.tax == Decimal("26.05")

    @pytest.mark.ac("S6-AC2")
    def test_total_formula_exact(self):
        """Total = subtotal - discount + shipping + tax (exact)"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        coupon = Coupon("SAVE10", "percent", Decimal("10"))
        quote = price_cart(lines, catalog, today=TODAY, coupon=coupon)

        expected_total = quote.subtotal - quote.discount + quote.shipping + quote.tax
        assert quote.total == expected_total

    @pytest.mark.ac("S6-AC2")
    def test_total_formula_with_multiple_discounts(self):
        """Total formula holds with volume and fixed coupon"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("10.00"))}
        lines = [Line("ITEM", 10)]  # Volume discount
        coupon = Coupon("MINUS5", "fixed", Decimal("5"))
        quote = price_cart(lines, catalog, today=TODAY, coupon=coupon)

        expected_total = quote.subtotal - quote.discount + quote.shipping + quote.tax
        assert quote.total == expected_total

    @pytest.mark.ac("S6-AC2")
    def test_total_formula_with_loyalty_and_coupon(self):
        """Total formula holds with loyalty and fixed coupon"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        customer = Customer(tier="gold")
        coupon = Coupon("MINUS3", "fixed", Decimal("3"))
        quote = price_cart(lines, catalog, today=TODAY, customer=customer, coupon=coupon)

        expected_total = quote.subtotal - quote.discount + quote.shipping + quote.tax
        assert quote.total == expected_total

    @pytest.mark.ac("S6-AC2")
    def test_total_formula_empty_cart(self):
        """Total formula on empty cart: all amounts are 0.00"""
        lines = []
        catalog = {}
        quote = price_cart(lines, catalog, today=TODAY)

        expected_total = quote.subtotal - quote.discount + quote.shipping + quote.tax
        assert quote.total == expected_total
        assert quote.total == Decimal("0.00")


class TestS6AC3Applied:
    """S6-AC3: applied lists volume:<SKU> (per SKU in order), then loyalty/coupon:%, then coupon:fixed."""

    @pytest.mark.ac("S6-AC3")
    def test_applied_volume_discount_listed(self):
        """applied contains volume:<SKU> for volume discounts"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("10.00"))}
        lines = [Line("ITEM", 10)]
        quote = price_cart(lines, catalog, today=TODAY)

        assert "volume:ITEM" in quote.applied

    @pytest.mark.ac("S6-AC3")
    def test_applied_multiple_volume_in_order_of_appearance(self):
        """Multiple volume discounts listed in order of first appearance"""
        catalog = {
            "A": Product("A", "A", Decimal("10.00")),
            "B": Product("B", "B", Decimal("10.00")),
            "C": Product("C", "C", Decimal("10.00")),
        }
        lines = [
            Line("B", 10),  # Appears first
            Line("A", 10),  # Appears second
            Line("C", 10),  # Appears third
        ]
        quote = price_cart(lines, catalog, today=TODAY)

        b_idx = quote.applied.index("volume:B")
        a_idx = quote.applied.index("volume:A")
        c_idx = quote.applied.index("volume:C")
        assert b_idx < a_idx < c_idx

    @pytest.mark.ac("S6-AC3")
    def test_applied_loyalty_listed(self):
        """applied contains 'loyalty' for loyalty discount"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        customer = Customer(tier="gold")
        quote = price_cart(lines, catalog, today=TODAY, customer=customer)

        assert "loyalty" in quote.applied

    @pytest.mark.ac("S6-AC3")
    def test_applied_percent_coupon_listed(self):
        """applied contains coupon:<CODE> for percent coupon"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        coupon = Coupon("SAVE10", "percent", Decimal("10"))
        quote = price_cart(lines, catalog, today=TODAY, coupon=coupon)

        assert "coupon:SAVE10" in quote.applied

    @pytest.mark.ac("S6-AC3")
    def test_applied_fixed_coupon_listed(self):
        """applied contains coupon:<CODE> for fixed coupon"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        coupon = Coupon("MINUS10", "fixed", Decimal("10"))
        quote = price_cart(lines, catalog, today=TODAY, coupon=coupon)

        assert "coupon:MINUS10" in quote.applied

    @pytest.mark.ac("S6-AC3")
    def test_applied_volume_before_percent_coupon(self):
        """applied order: volume discounts before percent coupon"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("10.00"))}
        lines = [Line("ITEM", 10)]
        coupon = Coupon("SAVE5", "percent", Decimal("5"))
        quote = price_cart(lines, catalog, today=TODAY, coupon=coupon)

        v_idx = quote.applied.index("volume:ITEM")
        c_idx = quote.applied.index("coupon:SAVE5")
        assert v_idx < c_idx

    @pytest.mark.ac("S6-AC3")
    def test_applied_loyalty_when_larger_than_coupon(self):
        """loyalty listed when larger than percent coupon"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        customer = Customer(tier="gold")  # 5%
        coupon = Coupon("SAVE3", "percent", Decimal("3"))
        quote = price_cart(lines, catalog, today=TODAY, customer=customer, coupon=coupon)

        assert "loyalty" in quote.applied
        assert "coupon:SAVE3" not in quote.applied

    @pytest.mark.ac("S6-AC3")
    def test_applied_coupon_when_larger_than_loyalty(self):
        """percent coupon listed when larger than loyalty"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        customer = Customer(tier="gold")  # 5%
        coupon = Coupon("SAVE10", "percent", Decimal("10"))
        quote = price_cart(lines, catalog, today=TODAY, customer=customer, coupon=coupon)

        assert "coupon:SAVE10" in quote.applied
        assert "loyalty" not in quote.applied

    @pytest.mark.ac("S6-AC3")
    def test_applied_coupon_when_equal_to_loyalty(self):
        """coupon listed when equal to loyalty (coupon wins tie)"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        customer = Customer(tier="gold")  # 5%
        coupon = Coupon("SAVE5", "percent", Decimal("5"))
        quote = price_cart(lines, catalog, today=TODAY, customer=customer, coupon=coupon)

        assert "coupon:SAVE5" in quote.applied
        assert "loyalty" not in quote.applied

    @pytest.mark.ac("S6-AC3")
    def test_applied_percent_discount_before_fixed_coupon(self):
        """percent discount before fixed coupon"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        customer = Customer(tier="gold")
        coupon = Coupon("MINUS5", "fixed", Decimal("5"))
        quote = price_cart(lines, catalog, today=TODAY, customer=customer, coupon=coupon)

        l_idx = quote.applied.index("loyalty")
        c_idx = quote.applied.index("coupon:MINUS5")
        assert l_idx < c_idx

    @pytest.mark.ac("S6-AC3")
    def test_applied_complete_order(self):
        """complete applied order: volume, loyalty, fixed coupon"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("10.00"))}
        lines = [Line("ITEM", 10)]
        customer = Customer(tier="gold")
        coupon = Coupon("MINUS5", "fixed", Decimal("5"))
        quote = price_cart(lines, catalog, today=TODAY, customer=customer, coupon=coupon)

        v_idx = quote.applied.index("volume:ITEM")
        l_idx = quote.applied.index("loyalty")
        c_idx = quote.applied.index("coupon:MINUS5")
        assert v_idx < l_idx < c_idx

    @pytest.mark.ac("S6-AC3")
    def test_applied_empty_when_no_discounts(self):
        """applied is empty tuple when no discounts apply"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("10.00"))}
        lines = [Line("ITEM", 1)]
        quote = price_cart(lines, catalog, today=TODAY)

        assert len(quote.applied) == 0
        assert quote.applied == ()
```