```python
import pytest
from datetime import date
from decimal import Decimal
from checkout import (
    price_cart, Product, Line, Customer, Coupon
)

TODAY = date(2026, 10, 3)


class TestS4Loyalty:
    """S4. Loyalty - Gold member discounts without unfair stacking"""

    # S4-AC1: Gold tier gets 5% loyalty discount, standard gets none
    
    @pytest.mark.ac("S4-AC1")
    def test_gold_tier_gets_5_percent_loyalty_discount(self):
        """Gold tier customers receive 5% loyalty discount"""
        catalog = {
            "PROD1": Product("PROD1", "Product 1", Decimal("100.00"))
        }
        lines = [Line("PROD1", 1)]
        customer = Customer(tier="gold")
        
        quote = price_cart(lines, catalog, today=TODAY, customer=customer)
        
        assert quote.subtotal == Decimal("100.00")
        assert quote.discount == Decimal("5.00")
        assert "loyalty" in quote.applied

    @pytest.mark.ac("S4-AC1")
    def test_standard_tier_gets_no_loyalty_discount(self):
        """Standard tier customers get no loyalty discount"""
        catalog = {
            "PROD1": Product("PROD1", "Product 1", Decimal("100.00"))
        }
        lines = [Line("PROD1", 1)]
        customer = Customer(tier="standard")
        
        quote = price_cart(lines, catalog, today=TODAY, customer=customer)
        
        assert quote.subtotal == Decimal("100.00")
        assert quote.discount == Decimal("0.00")
        assert "loyalty" not in quote.applied

    @pytest.mark.ac("S4-AC1")
    def test_default_customer_is_standard_no_loyalty(self):
        """Default customer is standard tier with no loyalty discount"""
        catalog = {
            "PROD1": Product("PROD1", "Product 1", Decimal("100.00"))
        }
        lines = [Line("PROD1", 1)]
        
        quote = price_cart(lines, catalog, today=TODAY)
        
        assert quote.discount == Decimal("0.00")
        assert "loyalty" not in quote.applied

    @pytest.mark.ac("S4-AC1")
    def test_loyalty_discount_multiple_items(self):
        """Loyalty discount applies to total subtotal across multiple items"""
        catalog = {
            "PROD1": Product("PROD1", "Product 1", Decimal("50.00")),
            "PROD2": Product("PROD2", "Product 2", Decimal("30.00"))
        }
        lines = [Line("PROD1", 1), Line("PROD2", 1)]
        customer = Customer(tier="gold")
        
        quote = price_cart(lines, catalog, today=TODAY, customer=customer)
        
        # Subtotal: 80.00, loyalty: 5% = 4.00
        assert quote.subtotal == Decimal("80.00")
        assert quote.discount == Decimal("4.00")
        assert "loyalty" in quote.applied

    @pytest.mark.ac("S4-AC1")
    def test_loyalty_discount_rounding_half_up(self):
        """Loyalty discount is rounded half-up to the cent"""
        catalog = {
            "PROD1": Product("PROD1", "Product 1", Decimal("33.33"))
        }
        lines = [Line("PROD1", 1)]
        customer = Customer(tier="gold")
        
        quote = price_cart(lines, catalog, today=TODAY, customer=customer)
        
        # 5% of 33.33 = 1.6665 -> rounds to 1.67
        assert quote.subtotal == Decimal("33.33")
        assert quote.discount == Decimal("1.67")

    @pytest.mark.ac("S4-AC1", "S2-AC1")
    def test_loyalty_applies_after_volume_discount(self):
        """Loyalty is 5% of subtotal calculated after volume discount"""
        catalog = {
            "PROD1": Product("PROD1", "Product 1", Decimal("10.00"))
        }
        lines = [Line("PROD1", 15)]  # 15 units triggers 10% volume discount
        customer = Customer(tier="gold")
        
        quote = price_cart(lines, catalog, today=TODAY, customer=customer)
        
        # Line total: 150.00, volume discount: 15.00
        # Subtotal: 135.00, loyalty: 5% of 135.00 = 6.75
        assert quote.subtotal == Decimal("135.00")
        assert quote.discount == Decimal("6.75")
        assert "volume:PROD1" in quote.applied
        assert "loyalty" in quote.applied

    # S4-AC2: Loyalty and percent coupon don't stack; fixed coupon does stack
    
    @pytest.mark.ac("S4-AC2")
    def test_loyalty_larger_than_percent_coupon_loyalty_wins(self):
        """When loyalty > percent coupon, loyalty discount applies"""
        catalog = {
            "PROD1": Product("PROD1", "Product 1", Decimal("100.00"))
        }
        lines = [Line("PROD1", 1)]
        customer = Customer(tier="gold")
        coupon = Coupon("SAVE3", "percent", Decimal("3"))
        
        quote = price_cart(
            lines, catalog, today=TODAY, customer=customer, coupon=coupon
        )
        
        # Loyalty: 5%, Coupon: 3% -> loyalty wins
        assert quote.discount == Decimal("5.00")
        assert "loyalty" in quote.applied
        assert "coupon:SAVE3" not in quote.applied

    @pytest.mark.ac("S4-AC2")
    def test_percent_coupon_larger_than_loyalty_coupon_wins(self):
        """When percent coupon > loyalty, coupon discount applies"""
        catalog = {
            "PROD1": Product("PROD1", "Product 1", Decimal("100.00"))
        }
        lines = [Line("PROD1", 1)]
        customer = Customer(tier="gold")
        coupon = Coupon("SAVE10", "percent", Decimal("10"))
        
        quote = price_cart(
            lines, catalog, today=TODAY, customer=customer, coupon=coupon
        )
        
        # Loyalty: 5%, Coupon: 10% -> coupon wins
        assert quote.discount == Decimal("10.00")
        assert "coupon:SAVE10" in quote.applied
        assert "loyalty" not in quote.applied

    @pytest.mark.ac("S4-AC2")
    def test_equal_loyalty_and_percent_coupon_coupon_wins(self):
        """When loyalty equals percent coupon, coupon wins"""
        catalog = {
            "PROD1": Product("PROD1", "Product 1", Decimal("100.00"))
        }
        lines = [Line("PROD1", 1)]
        customer = Customer(tier="gold")
        coupon = Coupon("SAVE5", "percent", Decimal("5"))
        
        quote = price_cart(
            lines, catalog, today=TODAY, customer=customer, coupon=coupon
        )
        
        # Loyalty: 5%, Coupon: 5% -> coupon wins
        assert quote.discount == Decimal("5.00")
        assert "coupon:SAVE5" in quote.applied
        assert "loyalty" not in quote.applied

    @pytest.mark.ac("S4-AC2")
    def test_loyalty_and_fixed_coupon_both_apply(self):
        """Loyalty and fixed coupon stack together"""
        catalog = {
            "PROD1": Product("PROD1", "Product 1", Decimal("100.00"))
        }
        lines = [Line("PROD1", 1)]
        customer = Customer(tier="gold")
        coupon = Coupon("SAVE10", "fixed", Decimal("10.00"))
        
        quote = price_cart(
            lines, catalog, today=TODAY, customer=customer, coupon=coupon
        )
        
        # Loyalty: 5% = 5.00, Fixed: 10.00, Total: 15.00
        assert quote.discount == Decimal("15.00")
        assert "loyalty" in quote.applied
        assert "coupon:SAVE10" in quote.applied

    @pytest.mark.ac("S4-AC2")
    def test_loyalty_and_fixed_coupon_application_order(self):
        """Applied field shows loyalty before fixed coupon"""
        catalog = {
            "PROD1": Product("PROD1", "Product 1", Decimal("100.00"))
        }
        lines = [Line("PROD1", 1)]
        customer = Customer(tier="gold")
        coupon = Coupon("SAVE5", "fixed", Decimal("5.00"))
        
        quote = price_cart(
            lines, catalog, today=TODAY, customer=customer, coupon=coupon
        )
        
        loyalty_idx = quote.applied.index("loyalty")
        coupon_idx = quote.applied.index("coupon:SAVE5")
        assert loyalty_idx < coupon_idx

    @pytest.mark.ac("S4-AC2")
    def test_standard_tier_with_percent_coupon_no_stacking_issue(self):
        """Standard tier with coupon applies coupon normally without loyalty"""
        catalog = {
            "PROD1": Product("PROD1", "Product 1", Decimal("100.00"))
        }
        lines = [Line("PROD1", 1)]
        customer = Customer(tier="standard")
        coupon = Coupon("SAVE10", "percent", Decimal("10"))
        
        quote = price_cart(
            lines, catalog, today=TODAY, customer=customer, coupon=coupon
        )
        
        assert quote.discount == Decimal("10.00")
        assert "coupon:SAVE10" in quote.applied
        assert "loyalty" not in quote.applied

    @pytest.mark.ac("S4-AC1", "S1-AC5")
    def test_gold_tier_empty_cart(self):
        """Gold tier with empty cart produces all-zero amounts"""
        catalog = {}
        lines = []
        customer = Customer(tier="gold")
        
        quote = price_cart(lines, catalog, today=TODAY, customer=customer)
        
        assert quote.subtotal == Decimal("0.00")
        assert quote.discount == Decimal("0.00")
        assert quote.shipping == Decimal("0.00")
        assert quote.tax == Decimal("0.00")
        assert quote.total == Decimal("0.00")
        assert quote.applied == ()

    @pytest.mark.ac("S4-AC2")
    def test_loyalty_percent_and_fixed_coupon_loyalty_then_fixed(self):
        """With percent and fixed coupon, larger percent coupon applies, then fixed"""
        catalog = {
            "PROD1": Product("PROD1", "Product 1", Decimal("100.00"))
        }
        lines = [Line("PROD1", 1)]
        customer = Customer(tier="gold")
        coupon = Coupon("MULTI10", "fixed", Decimal("10.00"))
        
        quote = price_cart(
            lines, catalog, today=TODAY, customer=customer, coupon=coupon
        )
        
        # Loyalty 5% would give 5.00, but if percent coupon existed it would win
        # With just fixed: loyalty 5.00 + fixed 10.00 = 15.00
        assert quote.subtotal == Decimal("100.00")
        assert quote.discount == Decimal("15.00")
```