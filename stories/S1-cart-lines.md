# S1. Cart lines

As a shopper, I want the cart to add up what I picked, and to tell me clearly when something in it can't be priced.

## Acceptance criteria

- **S1-AC1** Each line costs the product's unit price times the quantity. The subtotal is the sum of the line totals, after any volume discount (S2).
- **S1-AC2** A quantity must be a whole number from 1 to 99. Anything else (0, a negative number, 100 or more, a fraction, `True`) raises `CartError`.
- **S1-AC3** A line whose SKU is not in the catalog raises `CartError`.
- **S1-AC4** Lines with the same SKU are merged before pricing, adding up their quantities. The merged quantity must also be 99 or less, or `CartError` is raised.
- **S1-AC5** An empty cart costs nothing: every amount in the quote is 0.00, no shipping is charged, nothing is applied, and a coupon or loyalty tier is ignored.
