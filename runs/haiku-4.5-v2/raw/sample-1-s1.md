```python
import pytest
from decimal import Decimal
from datetime import date, timedelta
from checkout import (
    Product, Line, Customer, Coupon, CartError, CouponError, price_cart
)

# Test fixtures
CATALOG = {
    "BK-001": Product("BK-001", "Cookbook", Decimal("20.00"), "books"),
    "EL-001": Product("EL-001", "Laptop", Decimal("999.99"), "general"),
    "EL-002": Product("EL-002", "Mouse", Decimal("25.50"), "general"),
}

TODAY = date(2026, 10, 3)


# ============================================================================
# S1: Cart lines
# ============================================================================

class TestS1CartLines:
    """Tests for S1: Cart lines"""
    
    @pytest.mark.ac("S1-AC1")
    def test_single_line_cost(self):
        """S1-AC1: Unit price × quantity = line cost"""
        lines = [Line("EL-001", 2)]
        quote = price_cart(lines, CATALOG, today=TODAY)
        # EL-001: 999.99 × 2 = 1999.98
        assert quote.subtotal == Decimal("1999.98")
    
    @pytest.mark.ac("S1-AC1")
    def test_subtotal_sums_lines(self):
        """S1-AC1: Subtotal is sum of line totals"""
        lines = [
            Line("EL-001", 1),      # 999.99
            Line("EL-002", 2),      # 25.50 × 2 = 51.00
        ]
        quote = price_cart(lines, CATALOG, today=TODAY)
        # Total: 999.99 + 51.00 = 1050.99
        assert quote.subtotal == Decimal("1050.99")
    
    @pytest.mark.ac("S1-AC2")
    def test_quantity_minimum_valid(self):
        """S1-AC2: Quantity 1 is valid"""
        lines = [Line("EL-002", 1)]
        quote = price_cart(lines, CATALOG, today=TODAY)
        assert quote.subtotal == Decimal("25.50")
    
    @pytest.mark.ac("S1-AC2")
    def test_quantity_maximum_valid(self):
        """S1-AC2: Quantity 99 is valid"""
        lines = [Line("EL-002", 99)]
        quote = price_cart(lines, CATALOG, today=TODAY)
        # 25.50 × 99 = 2524.50
        assert quote.subtotal == Decimal("2524.50")
    
    @pytest.mark.ac("S1-AC2")
    def test_quantity_zero_raises_error(self):
        """S1-AC2: Quantity 0 raises CartError"""
        with pytest.raises(CartError):
            price_cart([Line("EL-001", 0)], CATALOG, today=TODAY)
    
    @pytest.mark.ac("S1-AC2")
    def test_quantity_negative_raises_error(self):
        """S1-AC2: Negative quantity raises CartError"""
        with pytest.raises(CartError):
            price_cart([Line("EL-001", -5)], CATALOG, today=TODAY)
    
    @pytest.mark.ac("S1-AC2")
    def test_quantity_100_raises_error(self):
        """S1-AC2: Quantity 100 raises CartError"""
        with pytest.raises(CartError):
            price_cart([Line("EL-001", 100)], CATALOG, today=TODAY)
    
    @pytest.mark.ac("S1-AC2")
    def test_quantity_very_high_raises_error(self):
        """S1-AC2: Very high quantity raises CartError"""
        with pytest.raises(CartError):
            price_cart([Line("EL-001", 999)], CATALOG, today=TODAY)
    
    @pytest.mark.ac("S1-AC2")
    def test_quantity_fraction_raises_error(self):
        """S1-AC2: Fractional quantity raises CartError"""
        with pytest.raises(CartError):
            price_cart([Line("EL-001", 1.5)], CATALOG, today=TODAY)
    
    @pytest.mark.ac("S1-AC2")
    def test_quantity_bool_true_raises_error(self):
        """S1-AC2: Quantity True raises CartError"""
        with pytest.raises(CartError):
            price_cart([Line("EL-001", True)], CATALOG, today=TODAY)
    
    @pytest.mark.ac("S1-AC3")
    def test_unknown_sku_raises_error(self):
        """S1-AC3: SKU not in catalog raises CartError"""
        with pytest.raises(CartError):
            price_cart([Line("UNKNOWN", 1)], CATALOG, today=TODAY)
    
    @pytest.mark.ac("S1-AC4")
    def test_lines_with_same_sku_merged(self):
        """S1-AC4: Lines with same SKU are merged"""
        lines = [Line("EL-001", 5), Line("EL-001", 3)]
        quote = price_cart(lines, CATALOG, today=TODAY)
        # Merged: 8 × 999.99 = 7999.92
        assert quote.subtotal == Decimal("7999.92")
    
    @pytest.mark.ac("S1-AC4")
    def test_merged_quantity_at_limit(self):
        """S1-AC4: Merged quantity of 99 is valid"""
        lines = [Line("EL-002", 49), Line("EL-002", 50)]
        quote = price_cart(lines, CATALOG, today=TODAY)
        # Merged: 99 × 25.50 = 2524.50
        assert quote.subtotal == Decimal("2524.50")
    
    @pytest.mark.ac("S1-AC4")
    def test_merged_quantity_100_raises_error(self):
        """S1-AC4: Merged quantity of 100 raises CartError"""
        with pytest.raises(CartError):
            price_cart([Line("EL-002", 50), Line("EL-002", 50)], CATALOG, today=TODAY)
    
    @pytest.mark.ac("S1-AC4")
    def test_merged_quantity_well_above_100_raises_error(self):
        """S1-AC4: Merged quantity well above 99 raises CartError"""
        with pytest.raises(CartError):
            price_cart([Line("EL-002", 60), Line("EL-002", 60)], CATALOG, today=TODAY)
    
    @pytest.mark.ac("S1-AC5")
    def test_empty_cart_all_amounts_zero(self):
        """S1-AC5: Empty cart has all amounts 0.00"""
        quote = price_cart([], CATALOG, today=TODAY)
        assert quote.subtotal == Decimal("0.00")
        assert quote.discount == Decimal("0.00")
        assert quote.shipping == Decimal("0.00")
        assert quote.tax == Decimal("0.00")
        assert quote.total == Decimal("0.00")
    
    @pytest.mark.ac("S1-AC5")
    def test_empty_cart_no_shipping_standard(self):
        """S1-AC5: Empty cart ignores shipping"""
        quote = price_cart([], CATALOG, today=TODAY, shipping="standard")
        assert quote.shipping == Decimal("0.00")
    
    @pytest.mark.ac("S1-AC5")
    def test_empty_cart_nothing_applied(self):
        """S1-AC5: Empty cart has nothing in applied"""
        quote = price_cart([], CATALOG, today=TODAY)
        assert quote.applied == ()
    
    @pytest.mark.ac("S1-AC5")
    def test_empty_cart_ignores_coupon(self):
        """S1-AC5: Empty cart ignores coupon"""
        coupon = Coupon("TEST", "percent", Decimal("10"))
        quote = price_cart([], CATALOG, today=TODAY, coupon=coupon)
        assert quote.discount == Decimal("0.00")
    
    @pytest.mark.ac("S1-AC5")
    def test_empty_cart_ignores_loyalty(self):
        """S1-AC5: Empty cart ignores loyalty tier"""
        customer = Customer("gold")
        quote = price_cart([], CATALOG, today=TODAY, customer=customer)
        assert quote.discount == Decimal("0.00")


# ============================================================================
# S2: Volume discount
# ============================================================================

class TestS2VolumeDiscount:
    """Tests for S2: Volume discount"""
    
    @pytest.mark.ac("S2-AC1")
    def test_10_units_10_percent_off(self):
        """S2-AC1: 10+ units get 10% off"""
        lines = [Line("EL-002", 10)]
        quote = price_cart(lines, CATALOG, today=TODAY)
        # 25.50 × 10 = 255.00; 10% off = 229.50
        assert quote.subtotal == Decimal("229.50")
        assert "volume:EL-002" in quote.applied
    
    @pytest.mark.ac("S2-AC1")
    def test_9_units_no_discount(self):
        """S2-AC1: 9 units get no volume discount"""
        lines = [Line("EL-002", 9)]
        quote = price_cart(lines, CATALOG, today=TODAY)
        # 25.50 × 9 = 229.50 (no discount)
        assert quote.subtotal == Decimal("229.50")
        assert "volume:EL-002" not in quote.applied
    
    @pytest.mark.ac("S2-AC1")
    def test_volume_discount_per_product(self):
        """S2-AC1: Volume discount applies per product"""
        lines = [
            Line("EL-002", 10),  # 255.00 → 229.50
            Line("BK-001", 5),   # 100.00 (no discount for books)
        ]
        quote = price_cart(lines, CATALOG, today=TODAY)
        # Total: 229.50 + 100.00 = 329.50
        assert quote.subtotal == Decimal("329.50")
    
    @pytest.mark.ac("S2-AC2")
    def test_50_units_15_percent_off(self):
        """S2-AC2: 50+ units get 15% off"""
        lines = [Line("EL-002", 50)]
        quote = price_cart(lines, CATALOG, today=TODAY)
        # 25.50 × 50 = 1275.00; 15% off = 1083.75
        assert quote.subtotal == Decimal("1083.75")
        assert "volume:EL-002" in quote.applied
    
    @pytest.mark.ac("S2-AC2")
    def test_49_units_10_percent_not_15(self):
        """S2-AC2: 49 units get 10% not 15%"""
        lines = [Line("EL-002", 49)]
        quote = price_cart(lines, CATALOG, today=TODAY)
        # 25.50 × 49 = 1249.50; 10% off = 1124.55
        assert quote.subtotal == Decimal("1124.55")
    
    @pytest.mark.ac("S2-AC3")
    def test_books_no_discount_at_10_units(self):
        """S2-AC3: Books get no volume discount even at 10+ units"""
        lines = [Line("BK-001", 10)]
        quote = price_cart(lines, CATALOG, today=TODAY)
        # 20.00 × 10 = 200.00 (no discount)
        assert quote.subtotal == Decimal("200.00")
        assert "volume:BK-001" not in quote.applied
    
    @pytest.mark.ac("S2-AC3")
    def test_books_no_discount_at_50_units(self):
        """S2-AC3: Books get no volume discount even at 50+ units"""
        lines = [Line("BK-001", 50)]
        quote = price_cart(lines, CATALOG, today=TODAY)
        # 20.00 × 50 = 1000.00 (no discount)
        assert quote.subtotal == Decimal("1000.00")
        assert "volume:BK-001" not in quote.applied


# ============================================================================
# S3: Coupons
# ============================================================================

class TestS3Coupons:
    """Tests for S3: Coupons"""
    
    @pytest.mark.ac("S3-AC1")
    def test_percent_coupon_applies_discount(self):
        """S3-AC1: Percent coupon takes value% off subtotal"""
        lines = [Line("EL-001", 1)]
        coupon = Coupon("SAVE10", "percent", Decimal("10"))
        quote = price_cart(lines, CATALOG, today=TODAY, coupon=coupon)
        # Subtotal: 999.99; 10% off = 99.999 → 100.00
        assert quote.discount == Decimal("100.00")
    
    @pytest.mark.ac("S3-AC1")
    def test_percent_coupon_50_percent(self):
        """S3-AC1: Percent coupon works for different percentages"""
        lines = [Line("EL-002", 2)]
        coupon = Coupon("HALF", "percent", Decimal("50"))
        quote = price_cart(lines, CATALOG, today=TODAY, coupon=coupon)
        # Subtotal: 51.00; 50% off = 25.50
        assert quote.discount == Decimal("25.50")
    
    @pytest.mark.ac("S3-AC2")
    def test_fixed_coupon_euros_off(self):
        """S3-AC2: Fixed coupon takes euros off"""
        lines = [Line("EL-001", 1)]
        coupon = Coupon("OFF20", "fixed", Decimal("20.00"))
        quote = price_cart(lines, CATALOG, today=TODAY, coupon=coupon)
        # Discount: 20.00
        assert quote.discount == Decimal("20.00")
    
    @pytest.mark.ac("S3-AC2")
    def test_fixed_coupon_never_negative(self):
        """S3-AC2: Fixed coupon never goes below 0.00"""
        lines = [Line("EL-002", 1)]
        coupon = Coupon("HUGE", "fixed", Decimal("100.00"))
        quote = price_cart(lines, CATALOG, today=TODAY, coupon=coupon)
        # Subtotal: 25.50; coupon capped at 25.50
        assert quote.discount == Decimal("25.50")
    
    @pytest.mark.ac("S3-AC3")
    def test_minimum_subtotal_met(self):
        """S3-AC3: Coupon applies when minimum subtotal is met"""
        lines = [Line("EL-002", 2)]
        coupon = Coupon("SAVE10", "percent", Decimal("10"), min_subtotal=Decimal("51.00"))
        quote = price_cart(lines, CATALOG, today=TODAY, coupon=coupon)
        # Subtotal: 51.00 ≥ 51.00 → applies
        assert quote.discount > Decimal("0")
    
    @pytest.mark.ac("S3-AC3")
    def test_minimum_subtotal_equal_applies(self):
        """S3-AC3: Coupon valid when subtotal equals minimum exactly"""
        lines = [Line("EL-002", 1)]
        coupon = Coupon("SAVE10", "percent", Decimal("10"), min_subtotal=Decimal("25.50"))
        quote = price_cart(lines, CATALOG, today=TODAY, coupon=coupon)
        # Subtotal: 25.50 = min_subtotal → applies
        assert quote.discount > Decimal("0")
    
    @pytest.mark.ac("S3-AC3")
    def test_minimum_subtotal_just_below_raises_error(self):
        """S3-AC3: Coupon fails when subtotal just below minimum"""
        lines = [Line("EL-002", 2)]
        coupon = Coupon("SAVE10", "percent", Decimal("10"), min_subtotal=Decimal("51.01"))
        with pytest.raises(CouponError):
            # Subtotal: 51.00 < 51.01
            price_cart(lines, CATALOG, today=TODAY, coupon=coupon)
    
    @pytest.mark.ac("S3-AC3")
    def test_minimum_subtotal_below_raises_error(self):
        """S3-AC3: Coupon raises CouponError when below minimum"""
        lines = [Line("EL-002", 1)]
        coupon = Coupon("SAVE10", "percent", Decimal("10"), min_subtotal=Decimal("50.00"))
        with pytest.raises(CouponError):
            # Subtotal: 25.50 < 50.00
            price_cart(lines, CATALOG, today=TODAY, coupon=coupon)
    
    @pytest.mark.ac("S3-AC4")
    def test_coupon_valid_on_expiry_date(self):
        """S3-AC4: Coupon is valid on its expiry date"""
        lines = [Line("EL-001", 1)]
        coupon = Coupon("SAVE10", "percent", Decimal("10"), expires=TODAY)
        quote = price_cart(lines, CATALOG, today=TODAY, coupon=coupon)
        assert quote.discount > Decimal("0")
    
    @pytest.mark.ac("S3-AC4")
    def test_coupon_invalid_day_after_expiry(self):
        """S3-AC4: Coupon raises error the day after expiry"""
        lines = [Line("EL-001", 1)]
        expiry = TODAY - timedelta(days=1)
        coupon = Coupon("SAVE10", "percent", Decimal("10"), expires=expiry)
        with pytest.raises(CouponError):
            price_cart(lines, CATALOG, today=TODAY, coupon=coupon)
    
    @pytest.mark.ac("S3-AC4")
    def test_coupon_no_expiry_date(self):
        """S3-AC4: Coupon without expiry date never expires"""
        lines = [Line("EL-001", 1)]
        coupon = Coupon("SAVE10", "percent", Decimal("10"), expires=None)
        quote = price_cart(lines, CATALOG, today=TODAY, coupon=coupon)
        assert quote.discount > Decimal("0")
    
    @pytest.mark.ac("S3-AC5")
    def test_invalid_coupon_kind_raises_error(self):
        """S3-AC5: Invalid coupon kind raises CouponError"""
        lines = [Line("EL-001", 1)]
        coupon = Coupon("BAD", "invalid", Decimal("10"))
        with pytest.raises(CouponError):
            price_cart(lines, CATALOG, today=TODAY, coupon=coupon)


# ============================================================================
# S4: Loyalty
# ============================================================================

class TestS4Loyalty:
    """Tests for S4: Loyalty"""
    
    @pytest.mark.ac("S4-AC1")
    def test_gold_tier_5_percent_discount(self):
        """S4-AC1: Gold tier gets 5% off subtotal"""
        lines = [Line("EL-001", 1)]
        customer = Customer("gold")
        quote = price_cart(lines, CATALOG, today=TODAY, customer=customer)
        # Subtotal: 999.99; 5% off = 49.9995 → 50.00
        assert quote.discount == Decimal("50.00")
    
    @pytest.mark.ac("S4-AC1")
    def test_standard_tier_no_discount(self):
        """S4-AC1: Standard tier gets no loyalty discount"""
        lines = [Line("EL-001", 1)]
        customer = Customer("standard")
        quote = price_cart(lines, CATALOG, today=TODAY, customer=customer)
        assert quote.discount == Decimal("0.00")
    
    @pytest.mark.ac("S4-AC2")
    def test_percent_coupon_larger_than_loyalty(self):
        """S4-AC2: Percent coupon larger than loyalty: use coupon"""
        lines = [Line("EL-001", 1)]
        coupon = Coupon("SAVE20", "percent", Decimal("20"))
        customer = Customer("gold")
        quote = price_cart(lines, CATALOG, today=TODAY, customer=customer, coupon=coupon)
        # Loyalty: 5% = 50.00
        # Coupon: 20% = 200.00
        # Use 200.00
        assert quote.discount == Decimal("200.00")
        assert "coupon:SAVE20" in quote.applied
        assert "loyalty" not in quote.applied
    
    @pytest.mark.ac("S4-AC2")
    def test_loyalty_larger_than_percent_coupon(self):
        """S4-AC2: Loyalty larger than percent coupon: use loyalty"""
        lines = [Line("EL-001", 1)]
        coupon = Coupon("SAVE3", "percent", Decimal("3"))
        customer = Customer("gold")
        quote = price_cart(lines, CATALOG, today=TODAY, customer=customer, coupon=coupon)
        # Loyalty: 5% = 50.00
        # Coupon: 3% = 30.00
        # Use 50.00
        assert quote.discount == Decimal("50.00")
        assert "loyalty" in quote.applied
        assert "coupon:SAVE3" not in quote.applied
    
    @pytest.mark.ac("S4-AC2")
    def test_percent_coupon_equals_loyalty_coupon_wins(self):
        """S4-AC2: Percent coupon equals loyalty: coupon wins"""
        lines = [Line("EL-001", 1)]
        coupon = Coupon("SAVE5", "percent", Decimal("5"))
        customer = Customer("gold")
        quote = price_cart(lines, CATALOG, today=TODAY, customer=customer, coupon=coupon)
        # Both 5%; coupon wins when equal
        assert "coupon:SAVE5" in quote.applied
        assert "loyalty" not in quote.applied
    
    @pytest.mark.ac("S4-AC2")
    def test_fixed_coupon_stacks_with_loyalty(self):
        """S4-AC2: Fixed coupon stacks with loyalty discount"""
        lines = [Line("EL-002", 2)]
        coupon = Coupon("OFF5", "fixed", Decimal("5.00"))
        customer = Customer("gold")
        quote = price_cart(lines, CATALOG, today=TODAY, customer=customer, coupon=coupon)
        # Subtotal: 51.00
        # Loyalty: 5% = 2.55
        # Fixed: 5.00
        # Total: 2.55 + 5.00 = 7.55
        assert quote.discount == Decimal("7.55")


# ============================================================================
# S5: Shipping
# ============================================================================

class TestS5Shipping:
    """Tests for S5: Shipping"""
    
    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_cost(self):
        """S5-AC1: Standard shipping costs 4.99"""
        lines = [Line("EL-002", 1)]
        quote = price_cart(lines, CATALOG, today=TODAY, shipping="standard")
        # Subtotal: 25.50 < 50.00
        assert quote.shipping == Decimal("4.99")
    
    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_free_at_50(self):
        """S5-AC1: Standard shipping free at 50.00+"""
        lines = [Line("EL-002", 2)]
        quote = price_cart(lines, CATALOG, today=TODAY, shipping="standard")
        # Subtotal: 51.00 ≥ 50.00
        assert quote.shipping == Decimal("0.00")
    
    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_exactly_50(self):
        """S5-AC1: Standard shipping free at exactly 50.00"""
        catalog = {
            "P-001": Product("P-001", "Item", Decimal("50.00"), "general")
        }
        lines = [Line("P-001", 1)]
        quote = price_cart(lines, catalog, today=TODAY, shipping="standard")
        # Subtotal: 50.00
        assert quote.shipping == Decimal("0.00")
    
    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_just_below_50(self):
        """S5-AC1: Standard shipping charged just below 50.00"""
        catalog = {
            "P-002": Product("P-002", "Item", Decimal("49.99"), "general")
        }
        lines = [Line("P-002", 1)]
        quote = price_cart(lines, catalog, today=TODAY, shipping="standard")
        # Subtotal: 49.99 < 50.00
        assert quote.shipping == Decimal("4.99")
    
    @pytest.mark.ac("S5-AC2")
    def test_express_shipping_cost(self):
        """S5-AC2: Express shipping costs 9.99"""
        lines = [Line("EL-002", 1)]
        quote = price_cart(lines, CATALOG, today=TODAY, shipping="express")
        assert quote.shipping == Decimal("9.99")
    
    @pytest.mark.ac("S5-AC2")
    def test_express_shipping_never_free(self):
        """S5-AC2: Express shipping never free"""
        lines = [Line("EL-001", 1)]
        quote = price_cart(lines, CATALOG, today=TODAY, shipping="express")
        # High subtotal, but express still costs 9.99
        assert quote.shipping == Decimal("9.99")
    
    @pytest.mark.ac("S5-AC3")
    def test_invalid_shipping_method_raises_error(self):
        """S5-AC3: Invalid shipping method raises CartError"""
        lines = [Line("EL-001", 1)]
        with pytest.raises(CartError):
            price_cart(lines, CATALOG, today=TODAY, shipping="invalid")


# ============================================================================
# S6: Tax, rounding and quote
# ============================================================================

class TestS6TaxRoundingQuote:
    """Tests for S6: Tax, rounding and quote"""
    
    @pytest.mark.ac("S6-AC1")
    def test_vat_21_percent_of_goods_and_shipping(self):
        """S6-AC1: VAT is 21% of goods after discounts plus shipping"""
        lines = [Line("EL-002", 1)]
        quote = price_cart(lines, CATALOG, today=TODAY, shipping="standard")
        # Subtotal: 25.50; no discount
        # Shipping: 4.99
        # VAT base: 25.50 + 4.99 = 30.49
        # VAT: 30.49 × 0.21 = 6.4029 → 6.40
        assert quote.tax == Decimal("6.40")
    
    @pytest.mark.ac("S6-AC1")
    def test_vat_with_discounted_goods(self):
        """S6-AC1: VAT based on discounted goods amount"""
        lines = [Line("EL-002", 10)]
        quote = price_cart(lines, CATALOG, today=TODAY, shipping="standard")
        # Subtotal: 255.00; 10% volume off = 229.50
        # Shipping: 4.99
        # VAT base: 229.50 + 4.99 = 234.49
        # VAT: 234.49 × 0.21 = 49.2429 → 49.24
        assert quote.tax == Decimal("49.24")
    
    @pytest.mark.ac("S6-AC2")
    def test_rounding_half_up_to_cent(self):
        """S6-AC2: Rounding is half-up to the cent"""
        catalog = {
            "P-003": Product("P-003", "Item", Decimal("10.01"), "general")
        }
        lines = [Line("P-003", 3)]
        coupon = Coupon("SAVE33", "percent", Decimal("33"))
        quote = price_cart(lines, catalog, today=TODAY, coupon=coupon)
        # Subtotal: 30.03
        # 33% off: 30.03 × 0.33 = 9.9099 → 9.91 (half-up)
        assert quote.discount == Decimal("9.91")
    
    @pytest.mark.ac("S6-AC2")
    def test_total_formula_exact(self):
        """S6-AC2: Total = subtotal - discount + shipping + tax"""
        lines = [Line("EL-002", 2)]
        coupon = Coupon("SAVE10", "percent", Decimal("10"))
        quote = price_cart(lines, CATALOG, today=TODAY, coupon=coupon, shipping="standard")
        # Subtotal: 51.00
        # Discount: 51.00 × 0.10 = 5.10
        # Goods after discount: 51.00 - 5.10 = 45.90
        # Shipping: 45.90 < 50.00 → 4.99
        # Tax: (45.90 + 4.99) × 0.21 = 50.89 × 0.21 = 10.6869 → 10.69
        # Total: 51.00 - 5.10 + 4.99 + 10.69 = 61.58
        expected = quote.subtotal - quote.discount + quote.shipping + quote.tax
        assert quote.total == expected
    
    @pytest.mark.ac("S6-AC3")
    def test_applied_volume_discounts_in_order(self):
        """S6-AC3: applied lists volume discounts in product appearance order"""
        lines = [
            Line("EL-001", 10),
            Line("EL-002", 10),
            Line("BK-001", 1),
        ]
        quote = price_cart(lines, CATALOG, today=TODAY)
        applied_list = list(quote.applied)
        # Should have volume:EL-001, then volume:EL-002
        assert applied_list[0] == "volume:EL-001"
        assert applied_list[1] == "volume:EL-002"
    
    @pytest.mark.ac("S6-AC3")
    def test_applied_loyalty_before_fixed_coupon(self):
        """S6-AC3: applied lists loyalty before fixed coupon"""
        lines = [Line("EL-001", 1)]
        coupon = Coupon("OFF10", "fixed", Decimal("10.00"))
        customer = Customer("gold")
        quote = price_cart(lines, CATALOG, today=TODAY, customer=customer, coupon=coupon)
        applied_list = list(quote.applied)
        # Find positions
        loyalty_idx = next((i for i, x in enumerate(applied_list) if x == "loyalty"), -1)
        coupon_idx = next((i for i, x in enumerate(applied_list) if x.startswith("coupon:")), -1)
        assert loyalty_idx >= 0 and coupon_idx >= 0
        assert loyalty_idx < coupon_idx
    
    @pytest.mark.ac("S6-AC3")
    def test_applied_percent_coupon_when_wins(self):
        """S6-AC3: applied lists percent coupon when it wins"""
        lines = [Line("EL-001", 1)]
        coupon = Coupon("SAVE10", "percent", Decimal("10"))
        customer = Customer("gold")
        quote = price_cart(lines, CATALOG, today=TODAY, customer=customer, coupon=coupon)
        # Coupon wins over loyalty
        assert "coupon:SAVE10" in quote.applied
        assert "loyalty" not in quote.applied
```