# Order Console — Requirements

## REQ-001 — View the order list
As an ops user I need a list of all orders so I can see what is in the pipeline.

- [ ] The list shows every order returned by `GET /orders`, newest first
- [ ] Each row shows order id, customer name, status and the grand total
- [ ] Orders can be filtered by status using the full backend status enum

## REQ-002 — Inspect an order's detail
As an ops user I need to drill into an Order to see its customer, line items and money breakdown.

- [ ] Detail view shows the nested customer object, all line items and the `amounts` breakdown
- [ ] Line items show SKU, quantity, unit price and line total

## REQ-003 — Manage the order status workflow
As an ops user I need to move an Order through its lifecycle without violating allowed transitions.

- [ ] Only legal status transitions for the current status are offered as actions
- [ ] A cancelled order shows a distinct badge and cannot be re-opened

## REQ-004 — Display the money breakdown including tax
As an ops user I need subtotal, tax, discount and total shown separately.

- [ ] All four amounts from `Order.amounts` are rendered with ISO currency formatting
- [ ] Totals reconcile to the business-rule calculation

## REQ-005 — Apply discount eligibility for premium customers
As a billing user I need discounts restricted to customers whose tier allows them.

- [ ] Discount controls are disabled unless the customer tier is `gold` or `platinum`
- [ ] Attempting an ineligible discount surfaces a validation error referencing the rule
