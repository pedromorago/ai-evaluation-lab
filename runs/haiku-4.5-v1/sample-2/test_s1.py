import pytest
from decimal import Decimal
from datetime import date
from checkout import (
    CartError,
    Product,
    Line,
    Customer,
    Coupon,
    price_cart,
)


class TestS1CartLines:
    """Tests for user story S1: Cart lines"""

    # S1-AC1: Each line costs unit price * quantity, subtotal is sum after volume discount

    @pytest.mark.ac("S1-AC1")
    def test_single_line_costs_unit_price_times_quantity(self):
        """Single line cost equals unit price times quantity."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10.00"))}
        lines = [Line(sku="PROD-1", quantity=5)]
        
        quote = price_cart(lines, catalog, today=date(2026, 1, 1))
        
        assert quote.subtotal == Decimal("50.00")

    @pytest.mark.ac("S1-AC1")
    def test_multiple_lines_sum_to_subtotal(self):
        """Subtotal is sum of all line totals."""
        catalog = {
            "PROD-1": Product(sku="PROD-1", name="P1", unit_price=Decimal("10.00")),
            "PROD-2": Product(sku="PROD-2", name="P2", unit_price=Decimal("20.00")),
        }
        lines = [
            Line(sku="PROD-1", quantity=2),
            Line(sku="PROD-2", quantity=3),
        ]
        
        quote = price_cart(lines, catalog, today=date(2026, 1, 1))
        
        # 2*10 + 3*20 = 80
        assert quote.subtotal == Decimal("80.00")

    @pytest.mark.ac("S1-AC1")
    def test_subtotal_after_volume_discount_10_units(self):
        """Subtotal reflects 10% volume discount at 10+ units."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10.00"))}
        lines = [Line(sku="PROD-1", quantity=10)]
        
        quote = price_cart(lines, catalog, today=date(2026, 1, 1))
        
        # 10 * 10 * (1 - 0.10) = 90
        assert quote.subtotal == Decimal("90.00")

    @pytest.mark.ac("S1-AC1")
    def test_subtotal_after_volume_discount_50_units(self):
        """Subtotal reflects 15% volume discount at 50+ units."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10.00"))}
        lines = [Line(sku="PROD-1", quantity=50)]
        
        quote = price_cart(lines, catalog, today=date(2026, 1, 1))
        
        # 50 * 10 * (1 - 0.15) = 425
        assert quote.subtotal == Decimal("425.00")

    @pytest.mark.ac("S1-AC1")
    def test_books_category_no_volume_discount(self):
        """Products in books category never get volume discount."""
        catalog = {
            "BOOK-1": Product(
                sku="BOOK-1",
                name="Book",
                unit_price=Decimal("10.00"),
                category="books"
            ),
        }
        lines = [Line(sku="BOOK-1", quantity=50)]
        
        quote = price_cart(lines, catalog, today=date(2026, 1, 1))
        
        # No discount for books even with 50 units
        assert quote.subtotal == Decimal("500.00")

    # S1-AC2: Quantity must be whole number 1-99, else CartError

    @pytest.mark.ac("S1-AC2")
    def test_quantity_zero_raises_cart_error(self):
        """Quantity of 0 raises CartError."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        
        with pytest.raises(CartError):
            price_cart([Line(sku="PROD-1", quantity=0)], catalog, today=date(2026, 1, 1))

    @pytest.mark.ac("S1-AC2")
    def test_negative_quantity_raises_cart_error(self):
        """Negative quantity raises CartError."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        
        with pytest.raises(CartError):
            price_cart([Line(sku="PROD-1", quantity=-5)], catalog, today=date(2026, 1, 1))

    @pytest.mark.ac("S1-AC2")
    def test_quantity_100_raises_cart_error(self):
        """Quantity of 100 raises CartError."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        
        with pytest.raises(CartError):
            price_cart([Line(sku="PROD-1", quantity=100)], catalog, today=date(2026, 1, 1))

    @pytest.mark.ac("S1-AC2")
    def test_quantity_over_100_raises_cart_error(self):
        """Quantity over 100 raises CartError."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        
        with pytest.raises(CartError):
            price_cart([Line(sku="PROD-1", quantity=150)], catalog, today=date(2026, 1, 1))

    @pytest.mark.ac("S1-AC2")
    def test_fractional_quantity_raises_cart_error(self):
        """Fractional quantity raises CartError."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        
        with pytest.raises(CartError):
            price_cart([Line(sku="PROD-1", quantity=5.5)], catalog, today=date(2026, 1, 1))

    @pytest.mark.ac("S1-AC2")
    def test_boolean_true_as_quantity_raises_cart_error(self):
        """Boolean True as quantity raises CartError."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        
        with pytest.raises(CartError):
            price_cart([Line(sku="PROD-1", quantity=True)], catalog, today=date(2026, 1, 1))

    @pytest.mark.ac("S1-AC2")
    def test_quantity_1_is_valid(self):
        """Quantity of 1 is valid."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        
        quote = price_cart([Line(sku="PROD-1", quantity=1)], catalog, today=date(2026, 1, 1))
        
        assert quote.subtotal == Decimal("10.00")

    @pytest.mark.ac("S1-AC2")
    def test_quantity_99_is_valid(self):
        """Quantity of 99 is valid."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        
        quote = price_cart([Line(sku="PROD-1", quantity=99)], catalog, today=date(2026, 1, 1))
        
        # 99 * 10 * (1 - 0.15) = 841.50
        assert quote.subtotal == Decimal("841.50")

    # S1-AC3: SKU not in catalog raises CartError

    @pytest.mark.ac("S1-AC3")
    def test_unknown_sku_raises_cart_error(self):
        """SKU not in catalog raises CartError."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        
        with pytest.raises(CartError):
            price_cart([Line(sku="UNKNOWN", quantity=5)], catalog, today=date(2026, 1, 1))

    @pytest.mark.ac("S1-AC3")
    def test_unknown_sku_with_valid_products_in_catalog(self):
        """Unknown SKU raises CartError even when other products exist."""
        catalog = {
            "PROD-1": Product(sku="PROD-1", name="P1", unit_price=Decimal("10")),
            "PROD-2": Product(sku="PROD-2", name="P2", unit_price=Decimal("20")),
        }
        
        with pytest.raises(CartError):
            price_cart([Line(sku="MISSING", quantity=5)], catalog, today=date(2026, 1, 1))

    # S1-AC4: Lines merged by SKU, merged quantity must be <= 99

    @pytest.mark.ac("S1-AC4")
    def test_same_sku_lines_are_merged_before_pricing(self):
        """Lines with same SKU are merged, quantities added."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        lines = [
            Line(sku="PROD-1", quantity=30),
            Line(sku="PROD-1", quantity=20),
        ]
        
        quote = price_cart(lines, catalog, today=date(2026, 1, 1))
        
        # Merged: 50, discount 15%
        # 50 * 10 * 0.85 = 425
        assert quote.subtotal == Decimal("425.00")

    @pytest.mark.ac("S1-AC4")
    def test_multiple_same_sku_lines_all_merged(self):
        """Three or more lines with same SKU are merged."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        lines = [
            Line(sku="PROD-1", quantity=20),
            Line(sku="PROD-1", quantity=15),
            Line(sku="PROD-1", quantity=15),
        ]
        
        quote = price_cart(lines, catalog, today=date(2026, 1, 1))
        
        # Merged: 50, discount 15%
        assert quote.subtotal == Decimal("425.00")

    @pytest.mark.ac("S1-AC4")
    def test_different_skus_not_merged(self):
        """Different SKUs are not merged for volume discount."""
        catalog = {
            "PROD-1": Product(sku="PROD-1", name="P1", unit_price=Decimal("10")),
            "PROD-2": Product(sku="PROD-2", name="P2", unit_price=Decimal("20")),
        }
        lines = [
            Line(sku="PROD-1", quantity=30),
            Line(sku="PROD-2", quantity=30),
        ]
        
        quote = price_cart(lines, catalog, today=date(2026, 1, 1))
        
        # Each product separately: 30*10*0.9 + 30*20*0.9 = 270 + 540 = 810
        assert quote.subtotal == Decimal("810.00")

    @pytest.mark.ac("S1-AC4")
    def test_merged_quantity_exactly_99_is_valid(self):
        """Merged quantity of exactly 99 is valid."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        lines = [
            Line(sku="PROD-1", quantity=50),
            Line(sku="PROD-1", quantity=49),
        ]
        
        quote = price_cart(lines, catalog, today=date(2026, 1, 1))
        
        # Merged: 99, discount 15%
        assert quote.subtotal == Decimal("841.50")

    @pytest.mark.ac("S1-AC4")
    def test_merged_quantity_100_raises_cart_error(self):
        """Merged quantity of 100 raises CartError."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        lines = [
            Line(sku="PROD-1", quantity=60),
            Line(sku="PROD-1", quantity=40),
        ]
        
        with pytest.raises(CartError):
            price_cart(lines, catalog, today=date(2026, 1, 1))

    @pytest.mark.ac("S1-AC4")
    def test_merged_quantity_over_100_raises_cart_error(self):
        """Merged quantity over 100 raises CartError."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        lines = [
            Line(sku="PROD-1", quantity=80),
            Line(sku="PROD-1", quantity=70),
        ]
        
        with pytest.raises(CartError):
            price_cart(lines, catalog, today=date(2026, 1, 1))

    # S1-AC5: Empty cart costs nothing

    @pytest.mark.ac("S1-AC5")
    def test_empty_cart_all_amounts_zero(self):
        """Empty cart has every amount at 0.00."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        
        quote = price_cart([], catalog, today=date(2026, 1, 1))
        
        assert quote.subtotal == Decimal("0.00")
        assert quote.discount == Decimal("0.00")
        assert quote.shipping == Decimal("0.00")
        assert quote.tax == Decimal("0.00")
        assert quote.total == Decimal("0.00")

    @pytest.mark.ac("S1-AC5")
    def test_empty_cart_no_standard_shipping_charged(self):
        """Empty cart has no standard shipping charged."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        
        quote = price_cart([], catalog, today=date(2026, 1, 1), shipping="standard")
        
        assert quote.shipping == Decimal("0.00")

    @pytest.mark.ac("S1-AC5")
    def test_empty_cart_no_express_shipping_charged(self):
        """Empty cart has no express shipping charged."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        
        quote = price_cart([], catalog, today=date(2026, 1, 1), shipping="express")
        
        assert quote.shipping == Decimal("0.00")

    @pytest.mark.ac("S1-AC5")
    def test_empty_cart_nothing_applied(self):
        """Empty cart has nothing in applied tuple."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        
        quote = price_cart([], catalog, today=date(2026, 1, 1))
        
        assert quote.applied == ()

    @pytest.mark.ac("S1-AC5")
    def test_empty_cart_ignores_percent_coupon(self):
        """Empty cart ignores percent coupon."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        coupon = Coupon(code="SAVE10", kind="percent", value=Decimal("10"))
        
        quote = price_cart([], catalog, today=date(2026, 1, 1), coupon=coupon)
        
        assert quote.discount == Decimal("0.00")
        assert quote.total == Decimal("0.00")

    @pytest.mark.ac("S1-AC5")
    def test_empty_cart_ignores_fixed_coupon(self):
        """Empty cart ignores fixed coupon."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        coupon = Coupon(code="SAVE5", kind="fixed", value=Decimal("5.00"))
        
        quote = price_cart([], catalog, today=date(2026, 1, 1), coupon=coupon)
        
        assert quote.discount == Decimal("0.00")
        assert quote.total == Decimal("0.00")

    @pytest.mark.ac("S1-AC5")
    def test_empty_cart_ignores_gold_loyalty_tier(self):
        """Empty cart ignores gold tier loyalty discount."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        customer = Customer(tier="gold")
        
        quote = price_cart([], catalog, today=date(2026, 1, 1), customer=customer)
        
        assert quote.discount == Decimal("0.00")
        assert quote.total == Decimal("0.00")

    @pytest.mark.ac("S1-AC5")
    def test_empty_cart_ignores_standard_loyalty_tier(self):
        """Empty cart ignores standard tier loyalty discount."""
        catalog = {"PROD-1": Product(sku="PROD-1", name="P", unit_price=Decimal("10"))}
        customer = Customer(tier="standard")
        
        quote = price_cart([], catalog, today=date(2026, 1, 1), customer=customer)
        
        assert quote.discount == Decimal("0.00")
        assert quote.total == Decimal("0.00")
