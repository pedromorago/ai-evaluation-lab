import pytest
from datetime import date
from decimal import Decimal
from checkout import Product, Line, Customer, Coupon, price_cart

TODAY = date(2026, 10, 3)


class TestLoyaltyBasic:
    """S4-AC1: Gold customers get 5% loyalty discount, standard customers get none."""

    @pytest.mark.ac("S4-AC1")
    def test_gold_customer_receives_loyalty_discount(self):
        """Gold tier customer gets loyalty discount applied."""
        product = Product(sku="BOOK-001", name="Python Guide", unit_price=Decimal("50"))
        catalog = {"BOOK-001": product}
        lines = [Line(sku="BOOK-001", quantity=1)]

        quote = price_cart(
            lines=lines,
            catalog=catalog,
            today=TODAY,
            customer=Customer(tier="gold"),
        )

        assert "loyalty" in quote.applied

    @pytest.mark.ac("S4-AC1")
    def test_standard_customer_no_loyalty_discount(self):
        """Standard tier customer does not get loyalty discount."""
        product = Product(sku="BOOK-001", name="Python Guide", unit_price=Decimal("50"))
        catalog = {"BOOK-001": product}
        lines = [Line(sku="BOOK-001", quantity=1)]

        quote = price_cart(
            lines=lines,
            catalog=catalog,
            today=TODAY,
            customer=Customer(tier="standard"),
        )

        assert "loyalty" not in quote.applied

    @pytest.mark.ac("S4-AC1")
    def test_default_customer_tier_is_standard(self):
        """Default customer tier is standard, no loyalty discount."""
        product = Product(sku="BOOK-001", name="Python Guide", unit_price=Decimal("50"))
        catalog = {"BOOK-001": product}
        lines = [Line(sku="BOOK-001", quantity=1)]

        quote = price_cart(
            lines=lines,
            catalog=catalog,
            today=TODAY,
            customer=Customer(),
        )

        assert "loyalty" not in quote.applied

    @pytest.mark.ac("S4-AC1")
    def test_gold_customer_empty_cart(self):
        """Gold customer with empty cart has no loyalty discount applied."""
        quote = price_cart(
            lines=[],
            catalog={},
            today=TODAY,
            customer=Customer(tier="gold"),
        )

        assert "loyalty" not in quote.applied


class TestLoyaltyVsPercentCoupon:
    """S4-AC2: Loyalty and percent coupon don't stack; only larger applies, coupon if equal."""

    @pytest.mark.ac("S4-AC2")
    def test_loyalty_5_percent_beats_coupon_3_percent(self):
        """When loyalty 5% > coupon 3%, only loyalty is applied."""
        product = Product(sku="BOOK-001", name="Python Guide", unit_price=Decimal("100"))
        catalog = {"BOOK-001": product}
        lines = [Line(sku="BOOK-001", quantity=1)]
        coupon = Coupon(code="SAVE3", kind="percent", value=Decimal("3"))

        quote = price_cart(
            lines=lines,
            catalog=catalog,
            today=TODAY,
            customer=Customer(tier="gold"),
            coupon=coupon,
        )

        assert "loyalty" in quote.applied
        assert "coupon:SAVE3" not in quote.applied

    @pytest.mark.ac("S4-AC2")
    def test_coupon_8_percent_beats_loyalty_5_percent(self):
        """When coupon 8% > loyalty 5%, only coupon is applied."""
        product = Product(sku="BOOK-001", name="Python Guide", unit_price=Decimal("100"))
        catalog = {"BOOK-001": product}
        lines = [Line(sku="BOOK-001", quantity=1)]
        coupon = Coupon(code="SAVE8", kind="percent", value=Decimal("8"))

        quote = price_cart(
            lines=lines,
            catalog=catalog,
            today=TODAY,
            customer=Customer(tier="gold"),
            coupon=coupon,
        )

        assert "coupon:SAVE8" in quote.applied
        assert "loyalty" not in quote.applied

    @pytest.mark.ac("S4-AC2")
    def test_equal_percent_discount_coupon_wins(self):
        """When loyalty 5% == coupon 5%, the coupon is applied."""
        product = Product(sku="BOOK-001", name="Python Guide", unit_price=Decimal("100"))
        catalog = {"BOOK-001": product}
        lines = [Line(sku="BOOK-001", quantity=1)]
        coupon = Coupon(code="SAVE5", kind="percent", value=Decimal("5"))

        quote = price_cart(
            lines=lines,
            catalog=catalog,
            today=TODAY,
            customer=Customer(tier="gold"),
            coupon=coupon,
        )

        assert "coupon:SAVE5" in quote.applied
        assert "loyalty" not in quote.applied

    @pytest.mark.ac("S4-AC2")
    def test_large_percent_coupon_beats_loyalty(self):
        """Large coupon percentage beats loyalty discount."""
        product = Product(sku="WIDGET", name="Widget", unit_price=Decimal("200"))
        catalog = {"WIDGET": product}
        lines = [Line(sku="WIDGET", quantity=1)]
        coupon = Coupon(code="SAVE15", kind="percent", value=Decimal("15"))

        quote = price_cart(
            lines=lines,
            catalog=catalog,
            today=TODAY,
            customer=Customer(tier="gold"),
            coupon=coupon,
        )

        assert "coupon:SAVE15" in quote.applied
        assert "loyalty" not in quote.applied


class TestLoyaltyWithFixedCoupon:
    """S4-AC2: Fixed coupon stacks with loyalty and is applied after it."""

    @pytest.mark.ac("S4-AC2")
    def test_fixed_coupon_stacks_with_loyalty(self):
        """Fixed coupon applies in addition to loyalty discount."""
        product = Product(sku="BOOK-001", name="Python Guide", unit_price=Decimal("100"))
        catalog = {"BOOK-001": product}
        lines = [Line(sku="BOOK-001", quantity=1)]
        coupon = Coupon(code="FLAT10", kind="fixed", value=Decimal("10"))

        quote = price_cart(
            lines=lines,
            catalog=catalog,
            today=TODAY,
            customer=Customer(tier="gold"),
            coupon=coupon,
        )

        assert "loyalty" in quote.applied
        assert "coupon:FLAT10" in quote.applied

    @pytest.mark.ac("S4-AC2")
    def test_fixed_coupon_after_loyalty_in_applied(self):
        """Fixed coupon appears after loyalty in applied tuple."""
        product = Product(sku="BOOK-001", name="Python Guide", unit_price=Decimal("100"))
        catalog = {"BOOK-001": product}
        lines = [Line(sku="BOOK-001", quantity=1)]
        coupon = Coupon(code="FLAT10", kind="fixed", value=Decimal("10"))

        quote = price_cart(
            lines=lines,
            catalog=catalog,
            today=TODAY,
            customer=Customer(tier="gold"),
            coupon=coupon,
        )

        loyalty_idx = quote.applied.index("loyalty")
        fixed_idx = quote.applied.index("coupon:FLAT10")
        assert loyalty_idx < fixed_idx

    @pytest.mark.ac("S4-AC2")
    def test_fixed_coupon_with_zero_loyalty_calculation(self):
        """Fixed coupon applies even when loyalty calculation would be minimal."""
        product = Product(sku="BOOK-001", name="Book", unit_price=Decimal("1"))
        catalog = {"BOOK-001": product}
        lines = [Line(sku="BOOK-001", quantity=1)]
        coupon = Coupon(code="FLAT1", kind="fixed", value=Decimal("1"))

        quote = price_cart(
            lines=lines,
            catalog=catalog,
            today=TODAY,
            customer=Customer(tier="gold"),
            coupon=coupon,
        )

        assert "loyalty" in quote.applied
        assert "coupon:FLAT1" in quote.applied


class TestLoyaltyIntegration:
    """Integration of loyalty with other features."""

    @pytest.mark.ac("S4-AC1")
    def test_loyalty_with_volume_discount(self):
        """Loyalty applies alongside volume discount."""
        product = Product(sku="BOOK-001", name="Python Guide", unit_price=Decimal("10"))
        catalog = {"BOOK-001": product}
        lines = [Line(sku="BOOK-001", quantity=10)]

        quote = price_cart(
            lines=lines,
            catalog=catalog,
            today=TODAY,
            customer=Customer(tier="gold"),
        )

        assert "volume:BOOK-001" in quote.applied
        assert "loyalty" in quote.applied
        # Volume discount comes first per S6-AC3
        volume_idx = quote.applied.index("volume:BOOK-001")
        loyalty_idx = quote.applied.index("loyalty")
        assert volume_idx < loyalty_idx

    @pytest.mark.ac("S4-AC1")
    def test_loyalty_multiple_products(self):
        """Loyalty applies when cart has multiple products."""
        product1 = Product(sku="SKU-1", name="Product 1", unit_price=Decimal("50"))
        product2 = Product(sku="SKU-2", name="Product 2", unit_price=Decimal("30"))
        catalog = {"SKU-1": product1, "SKU-2": product2}
        lines = [Line(sku="SKU-1", quantity=1), Line(sku="SKU-2", quantity=1)]

        quote = price_cart(
            lines=lines,
            catalog=catalog,
            today=TODAY,
            customer=Customer(tier="gold"),
        )

        assert "loyalty" in quote.applied

    @pytest.mark.ac("S4-AC2")
    def test_fixed_coupon_with_standard_customer(self):
        """Standard customer can use fixed coupon without loyalty."""
        product = Product(sku="BOOK-001", name="Python Guide", unit_price=Decimal("100"))
        catalog = {"BOOK-001": product}
        lines = [Line(sku="BOOK-001", quantity=1)]
        coupon = Coupon(code="FLAT5", kind="fixed", value=Decimal("5"))

        quote = price_cart(
            lines=lines,
            catalog=catalog,
            today=TODAY,
            customer=Customer(tier="standard"),
            coupon=coupon,
        )

        assert "loyalty" not in quote.applied
        assert "coupon:FLAT5" in quote.applied

    @pytest.mark.ac("S4-AC2")
    def test_standard_customer_with_percent_coupon(self):
        """Standard customer can use percent coupon."""
        product = Product(sku="BOOK-001", name="Python Guide", unit_price=Decimal("100"))
        catalog = {"BOOK-001": product}
        lines = [Line(sku="BOOK-001", quantity=1)]
        coupon = Coupon(code="SAVE10", kind="percent", value=Decimal("10"))

        quote = price_cart(
            lines=lines,
            catalog=catalog,
            today=TODAY,
            customer=Customer(tier="standard"),
            coupon=coupon,
        )

        assert "loyalty" not in quote.applied
        assert "coupon:SAVE10" in quote.applied
