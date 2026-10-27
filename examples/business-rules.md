# Order Console — Business Rules

### BR-001 — Order grand total reconciliation
The order grand total must equal subtotal plus tax minus discount. The UI must
render the server-computed amounts rather than recomputing them client-side.

- Applies to: Order
- Requires fields: Order.amounts
- Acceptance:
  - given an Order with subtotal, tax and discount, when the summary renders, then total equals subtotal + tax - discount
  - given a missing amounts object, when the order renders, then a safe placeholder is shown

### BR-002 — Tax calculation
Tax is computed by the billing service at the prevailing rate on (subtotal minus
discount); the UI never calculates tax itself.

- Applies to: Order
- Requires fields: Order.amounts
- Acceptance:
  - given any order, when displayed, then the tax value shown is exactly the value from the contract payload

### BR-003 — Order status transition guard
Allowed transitions are pending -> paid -> shipped -> delivered. An order may be
cancelled only from pending or paid. Any other transition is rejected.

- Applies to: Order
- Requires fields: Order.status
- Acceptance:
  - given a pending order, when acting on it, then only paid and cancelled are offered
  - given a delivered order, when acting on it, then no transitions are offered
  - given an unknown status value, when rendering, then a fallback badge is shown without crashing

### BR-004 — Discount eligibility
A discount may be applied only when the linked customer's tier is `gold` or
`platinum`; silver and bronze customers are ineligible.

- Applies to: Order, Customer
- Requires fields: Order.amounts, Customer.tier
- Acceptance:
  - given a silver customer, when an operator tries a discount, then the action is blocked with a rule reference
  - given a gold customer, when a discount is applied, then amounts.discount is reflected in the total

### BR-005 — Currency handling
All monetary values are expressed using an ISO 4217 currency code; `USD` is the
default when the backend omits the field. Money is formatted with that code.

- Applies to: Order
- Requires fields: Order.currency
- Acceptance:
  - given currency USD, when totals render, then they use USD currency formatting
  - given a missing currency, when totals render, then USD is assumed
