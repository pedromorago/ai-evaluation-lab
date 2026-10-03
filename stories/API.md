# Public API of the `checkout` package

Everything below is importable from `checkout`. Amounts are `decimal.Decimal` in euros.

```python
from datetime import date
from decimal import Decimal

class CartError(ValueError): ...
class CouponError(CartError): ...

@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    unit_price: Decimal
    category: str = "general"      # "general" or "books"

@dataclass(frozen=True)
class Line:
    sku: str
    quantity: int

@dataclass(frozen=True)
class Customer:
    tier: str = "standard"         # "standard" or "gold"

@dataclass(frozen=True)
class Coupon:
    code: str
    kind: str                      # "percent" or "fixed"
    value: Decimal                 # percent: 10 means 10% off; fixed: euros off
    min_subtotal: Decimal = Decimal("0")
    expires: date | None = None    # last day the coupon is valid

@dataclass(frozen=True)
class Quote:
    subtotal: Decimal              # line totals after volume discounts
    discount: Decimal              # coupon and loyalty discounts together
    shipping: Decimal
    tax: Decimal
    total: Decimal
    applied: tuple[str, ...]       # e.g. ("volume:BK-1", "loyalty", "coupon:SAVE10")

def price_cart(
    lines: list[Line],
    catalog: dict[str, Product],   # SKU -> Product
    *,
    today: date,
    customer: Customer = Customer(),
    coupon: Coupon | None = None,
    shipping: str = "standard",    # "standard" or "express"
) -> Quote: ...
```

`price_cart` has no side effects and does not read the clock: the date always comes from `today`.
