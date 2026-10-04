import pytest
from datetime import date
from decimal import Decimal
from checkout import price_cart, Product, Line, Customer, Coupon, CartError


class TestS5Shipping:
    """Tests for shipping costs and free shipping threshold."""
    
    # S5-AC1: Standard shipping costs 4.99, and is free when the goods,
    # after all discounts, come to 50.00 or more.
    
    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_costs_4_99_when_below_threshold(self):
        """Standard shipping costs 4.99 when goods after discounts are below 50.00"""
        catalog = {"PROD-1": Product("PROD-1", "Product 1", Decimal("40.00"))}
        lines = [Line("PROD-1", 1)]
        
        quote = price_cart(
            lines,
            catalog,
            today=date(2026, 1, 1),
            shipping="standard"
        )
        
        assert quote.shipping == Decimal("4.99")
    
    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_free_when_goods_equal_50(self):
        """Standard shipping is free when goods after discounts equal 50.00"""
        catalog = {"PROD-1": Product("PROD-1", "Product 1", Decimal("50.00"))}
        lines = [Line("PROD-1", 1)]
        
        quote = price_cart(
            lines,
            catalog,
            today=date(2026, 1, 1),
            shipping="standard"
        )
        
        assert quote.shipping == Decimal("0.00")
    
    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_free_when_goods_exceed_50(self):
        """Standard shipping is free when goods after discounts exceed 50.00"""
        catalog = {"PROD-1": Product("PROD-1", "Product 1", Decimal("60.00"))}
        lines = [Line("PROD-1", 1)]
        
        quote = price_cart(
            lines,
            catalog,
            today=date(2026, 1, 1),
            shipping="standard"
        )
        
        assert quote.shipping == Decimal("0.00")
    
    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_threshold_after_percent_coupon(self):
        """Standard shipping threshold is applied after percent coupon discount"""
        # Subtotal 60.00, 10% coupon = 6.00 discount
        # Goods after discounts: 54.00 >= 50.00 -> free shipping
        catalog = {"PROD-1": Product("PROD-1", "Product 1", Decimal("60.00"))}
        lines = [Line("PROD-1", 1)]
        coupon = Coupon("SAVE10", "percent", Decimal("10"))
        
        quote = price_cart(
            lines,
            catalog,
            today=date(2026, 1, 1),
            shipping="standard",
            coupon=coupon
        )
        
        assert quote.shipping == Decimal("0.00")
    
    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_threshold_after_loyalty_discount(self):
        """Standard shipping threshold is applied after loyalty discount"""
        # Gold customer, subtotal 55.00, 5% loyalty = 2.75 discount
        # Goods after discounts: 52.25 >= 50.00 -> free shipping
        catalog = {"PROD-1": Product("PROD-1", "Product 1", Decimal("55.00"))}
        lines = [Line("PROD-1", 1)]
        customer = Customer(tier="gold")
        
        quote = price_cart(
            lines,
            catalog,
            today=date(2026, 1, 1),
            customer=customer,
            shipping="standard"
        )
        
        assert quote.shipping == Decimal("0.00")
    
    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_charged_when_below_threshold_with_discount(self):
        """Standard shipping is charged when below threshold even with discounts"""
        # Gold customer, subtotal 45.00, 5% loyalty = 2.25 discount
        # Goods after discounts: 42.75 < 50.00 -> charged shipping
        catalog = {"PROD-1": Product("PROD-1", "Product 1", Decimal("45.00"))}
        lines = [Line("PROD-1", 1)]
        customer = Customer(tier="gold")
        
        quote = price_cart(
            lines,
            catalog,
            today=date(2026, 1, 1),
            customer=customer,
            shipping="standard"
        )
        
        assert quote.shipping == Decimal("4.99")
    
    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_boundary_just_below_50(self):
        """Standard shipping is charged when goods are just below 50.00"""
        catalog = {"PROD-1": Product("PROD-1", "Product 1", Decimal("49.99"))}
        lines = [Line("PROD-1", 1)]
        
        quote = price_cart(
            lines,
            catalog,
            today=date(2026, 1, 1),
            shipping="standard"
        )
        
        assert quote.shipping == Decimal("4.99")
    
    @pytest.mark.ac("S5-AC1")
    def test_standard_shipping_threshold_across_multiple_lines(self):
        """Standard shipping threshold applies across multiple lines"""
        # Two products: 30.00 + 25.00 = 55.00 >= 50.00 -> free
        catalog = {
            "PROD-1": Product("PROD-1", "Product 1", Decimal("30.00")),
            "PROD-2": Product("PROD-2", "Product 2", Decimal("25.00"))
        }
        lines = [Line("PROD-1", 1), Line("PROD-2", 1)]
        
        quote = price_cart(
            lines,
            catalog,
            today=date(2026, 1, 1),
            shipping="standard"
        )
        
        assert quote.shipping == Decimal("0.00")
    
    # S5-AC2: Express shipping costs 9.99 and is never free.
    
    @pytest.mark.ac("S5-AC2")
    def test_express_shipping_costs_9_99(self):
        """Express shipping costs 9.99"""
        catalog = {"PROD-1": Product("PROD-1", "Product 1", Decimal("10.00"))}
        lines = [Line("PROD-1", 1)]
        
        quote = price_cart(
            lines,
            catalog,
            today=date(2026, 1, 1),
            shipping="express"
        )
        
        assert quote.shipping == Decimal("9.99")
    
    @pytest.mark.ac("S5-AC2")
    def test_express_shipping_never_free_with_high_subtotal(self):
        """Express shipping is never free, even with high subtotal"""
        catalog = {"PROD-1": Product("PROD-1", "Product 1", Decimal("1000.00"))}
        lines = [Line("PROD-1", 1)]
        
        quote = price_cart(
            lines,
            catalog,
            today=date(2026, 1, 1),
            shipping="express"
        )
        
        assert quote.shipping == Decimal("9.99")
    
    @pytest.mark.ac("S5-AC2")
    def test_express_shipping_never_free_with_discounts(self):
        """Express shipping is never free, even with coupon and loyalty"""
        catalog = {"PROD-1": Product("PROD-1", "Product 1", Decimal("100.00"))}
        lines = [Line("PROD-1", 1)]
        customer = Customer(tier="gold")
        coupon = Coupon("SAVE10", "percent", Decimal("10"))
        
        quote = price_cart(
            lines,
            catalog,
            today=date(2026, 1, 1),
            customer=customer,
            coupon=coupon,
            shipping="express"
        )
        
        assert quote.shipping == Decimal("9.99")
    
    # S5-AC3: Any other shipping method raises CartError.
    
    @pytest.mark.ac("S5-AC3")
    def test_invalid_shipping_method_raises_error(self):
        """Invalid shipping method raises CartError"""
        catalog = {"PROD-1": Product("PROD-1", "Product 1", Decimal("10.00"))}
        lines = [Line("PROD-1", 1)]
        
        with pytest.raises(CartError):
            price_cart(
                lines,
                catalog,
                today=date(2026, 1, 1),
                shipping="invalid"
            )
    
    @pytest.mark.ac("S5-AC3")
    def test_overnight_shipping_raises_error(self):
        """Another invalid shipping method raises CartError"""
        catalog = {"PROD-1": Product("PROD-1", "Product 1", Decimal("10.00"))}
        lines = [Line("PROD-1", 1)]
        
        with pytest.raises(CartError):
            price_cart(
                lines,
                catalog,
                today=date(2026, 1, 1),
                shipping="overnight"
            )
    
    @pytest.mark.ac("S5-AC3")
    def test_empty_shipping_method_raises_error(self):
        """Empty string shipping method raises CartError"""
        catalog = {"PROD-1": Product("PROD-1", "Product 1", Decimal("10.00"))}
        lines = [Line("PROD-1", 1)]
        
        with pytest.raises(CartError):
            price_cart(
                lines,
                catalog,
                today=date(2026, 1, 1),
                shipping=""
            )
