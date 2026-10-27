# SPEC-R01 — Implement business rule BR-001 — Order grand total reconciliation

- **Scope:** cross_cutting
- **Target entity:** Order
- **Business rules:** BR-001
- **Requirements:** REQ-001, REQ-002, REQ-003, REQ-004, REQ-005

## Current state
The order grand total must equal subtotal plus tax minus discount. The UI must render the server-computed amounts rather than recomputing them client-side.

## Target state
Rule BR-001 enforced and covered by automated tests.

## Required changes
- Encode BR-001 in the domain/adapter layer (keep it out of presentational components).
- Required fields: Order.amounts.

## Acceptance criteria
- [ ] given an Order with subtotal, tax and discount, when the summary renders, then total equals subtotal + tax - discount
- [ ] given a missing amounts object, when the order renders, then a safe placeholder is shown

## Evidence
- Target field 'amounts' (object) is not represented in the UI.
- BR-001 requires 'amounts' but the UI currently has required_missing (—).
