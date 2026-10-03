# S6. Tax, rounding and the quote

As a shopper, I want a total I can check by hand.

## Acceptance criteria

- **S6-AC1** VAT is 21% of the goods after discounts plus shipping.
- **S6-AC2** Every amount in the quote is rounded half up to the cent: the subtotal, then each discount, then the tax. The total is exactly subtotal − discount + shipping + tax.
- **S6-AC3** `applied` lists what was applied, in this order: `volume:<SKU>` for each discounted product in the order the products first appear in the cart, then `loyalty` or `coupon:<CODE>` for the percentage discount that won, then `coupon:<CODE>` for a fixed coupon.
