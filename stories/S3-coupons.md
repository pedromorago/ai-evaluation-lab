# S3. Coupons

As a shopper with a coupon code, I want the discount it promises, and a clear error when it doesn't apply.

## Acceptance criteria

- **S3-AC1** A `percent` coupon takes its value as a percentage off the subtotal (value 10 means 10% off).
- **S3-AC2** A `fixed` coupon takes its value in euros off, after any percentage discount, and never takes the goods below 0.00.
- **S3-AC3** A coupon with a minimum subtotal raises `CouponError` when the subtotal is below it. A subtotal equal to the minimum is enough.
- **S3-AC4** A coupon raises `CouponError` after its expiry date. It is still valid on the expiry date itself. A coupon without an expiry date never expires.
- **S3-AC5** A coupon whose kind is neither `percent` nor `fixed` raises `CouponError`.

`CouponError` is a subclass of `CartError`.
