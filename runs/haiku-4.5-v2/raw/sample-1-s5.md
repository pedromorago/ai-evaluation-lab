```python
import pytest
from decimal import Decimal
from datetime import date
from checkout import CartError, Product, Line, Customer, Coupon, price_cart

TODAY = date(2026, 10, 3)


class TestS5AC1StandardShipping:
    """S5-AC1: Standard shipping costs 4.99, free when goods >= 50.00"""

    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_costs_4_99_on_small_order(self):
        """Standard shipping should cost 4.99 when goods < 50.00"""
        # goods = 40.00, so shipping = 4.99
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("40.00"))}
        lines = [Line("ITEM", 1)]

        quote = price_cart(lines, catalog, today=TODAY, shipping="standard")

        assert quote.shipping == Decimal("4.99")

    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_costs_4_99_just_below_threshold(self):
        """Standard shipping should cost 4.99 when goods = 49.99"""
        # goods = 49.99, so shipping = 4.99
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("49.99"))}
        lines = [Line("ITEM", 1)]

        quote = price_cart(lines, catalog, today=TODAY, shipping="standard")

        assert quote.shipping == Decimal("4.99")

    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_free_at_threshold(self):
        """Standard shipping should be free when goods = 50.00"""
        # goods = 50.00, so shipping = 0.00
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("50.00"))}
        lines = [Line("ITEM", 1)]

        quote = price_cart(lines, catalog, today=TODAY, shipping="standard")

        assert quote.shipping == Decimal("0.00")

    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_free_above_threshold(self):
        """Standard shipping should be free when goods > 50.00"""
        # goods = 65.00, so shipping = 0.00
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("65.00"))}
        lines = [Line("ITEM", 1)]

        quote = price_cart(lines, catalog, today=TODAY, shipping="standard")

        assert quote.shipping == Decimal("0.00")

    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_with_multiple_items_at_threshold(self):
        """Standard shipping free when multiple items sum to 50.00"""
        # goods = 25.00 + 25.00 = 50.00, so shipping = 0.00
        catalog = {
            "ITEM1": Product("ITEM1", "Item 1", Decimal("25.00")),
            "ITEM2": Product("ITEM2", "Item 2", Decimal("25.00")),
        }
        lines = [Line("ITEM1", 1), Line("ITEM2", 1)]

        quote = price_cart(lines, catalog, today=TODAY, shipping="standard")

        assert quote.shipping == Decimal("0.00")

    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_threshold_after_fixed_coupon(self):
        """Standard shipping free when fixed coupon discount keeps goods >= 50.00"""
        # subtotal = 100.00, fixed coupon -50.00
        # goods = 100.00 - 50.00 = 50.00, so shipping = 0.00
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]
        coupon = Coupon("SAVE50", "fixed", Decimal("50.00"))

        quote = price_cart(
            lines, catalog, today=TODAY, coupon=coupon, shipping="standard"
        )

        assert quote.shipping == Decimal("0.00")

    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_charged_when_percent_coupon_below_threshold(self):
        """Standard shipping charged when percent coupon brings goods below 50.00"""
        # subtotal = 55.00, 10% coupon discount = 5.50
        # goods = 55.00 - 5.50 = 49.50 < 50.00, so shipping = 4.99
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("55.00"))}
        lines = [Line("ITEM", 1)]
        coupon = Coupon("SAVE10", "percent", Decimal("10"))

        quote = price_cart(
            lines, catalog, today=TODAY, coupon=coupon, shipping="standard"
        )

        assert quote.shipping == Decimal("4.99")

    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_threshold_after_loyalty_discount(self):
        """Standard shipping free when loyalty discount keeps goods >= 50.00"""
        # subtotal = 55.00, gold tier 5% loyalty discount = 2.75
        # goods = 55.00 - 2.75 = 52.25 >= 50.00, so shipping = 0.00
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("55.00"))}
        lines = [Line("ITEM", 1)]
        customer = Customer(tier="gold")

        quote = price_cart(
            lines, catalog, today=TODAY, customer=customer, shipping="standard"
        )

        assert quote.shipping == Decimal("0.00")

    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_charged_with_volume_discount_below_threshold(self):
        """Standard shipping charged when volume discount brings goods below 50.00"""
        # 10 units at 5.00 each = 50.00 base
        # 10% volume discount on entire line: 50.00 * 0.9 = 45.00
        # goods = 45.00 < 50.00, so shipping = 4.99
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("5.00"))}
        lines = [Line("ITEM", 10)]

        quote = price_cart(lines, catalog, today=TODAY, shipping="standard")

        assert quote.shipping == Decimal("4.99")


class TestS5AC2ExpressShipping:
    """S5-AC2: Express shipping costs 9.99 and is never free"""

    @pytest.mark.ac("S5-AC2")
    def test_express_shipping_costs_9_99_on_small_order(self):
        """Express shipping should cost 9.99 on small orders"""
        # goods = 10.00, shipping = 9.99
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("10.00"))}
        lines = [Line("ITEM", 1)]

        quote = price_cart(lines, catalog, today=TODAY, shipping="express")

        assert quote.shipping == Decimal("9.99")

    @pytest.mark.ac("S5-AC2")
    def test_express_shipping_costs_9_99_on_large_order(self):
        """Express shipping never free, even on large orders"""
        # goods = 100.00, shipping = 9.99 (never free)
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("100.00"))}
        lines = [Line("ITEM", 1)]

        quote = price_cart(lines, catalog, today=TODAY, shipping="express")

        assert quote.shipping == Decimal("9.99")

    @pytest.mark.ac("S5-AC2")
    def test_express_shipping_costs_9_99_at_standard_free_threshold(self):
        """Express shipping costs 9.99 even when standard would be free"""
        # goods = 50.00 (standard shipping would be free)
        # express still costs 9.99 (never free)
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("50.00"))}
        lines = [Line("ITEM", 1)]

        quote = price_cart(lines, catalog, today=TODAY, shipping="express")

        assert quote.shipping == Decimal("9.99")


class TestS5AC3InvalidShipping:
    """S5-AC3: Any other shipping method raises CartError"""

    @pytest.mark.ac("S5-AC3")
    def test_invalid_shipping_method_raises_cartError(self):
        """Invalid shipping method should raise CartError"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("10.00"))}
        lines = [Line("ITEM", 1)]

        with pytest.raises(CartError):
            price_cart(lines, catalog, today=TODAY, shipping="invalid")

    @pytest.mark.ac("S5-AC3")
    def test_unknown_shipping_method_raises_cartError(self):
        """Unknown shipping method should raise CartError"""
        catalog = {"ITEM": Product("ITEM", "Item", Decimal("20.00"))}
        lines = [Line("ITEM", 1)]

        with pytest.raises(CartError):
            price_cart(lines, catalog, today=TODAY, shipping="overnight")
```