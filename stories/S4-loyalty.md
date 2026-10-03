# S4. Loyalty

As a gold member, I want my loyalty discount, without it stacking unfairly with other promotions.

## Acceptance criteria

- **S4-AC1** Customers in the `gold` tier get 5% off the subtotal. `standard` customers get no loyalty discount.
- **S4-AC2** The loyalty discount and a `percent` coupon don't stack: only the larger of the two applies, and the coupon if they are equal. A `fixed` coupon does stack with the loyalty discount, and is taken off after it.
