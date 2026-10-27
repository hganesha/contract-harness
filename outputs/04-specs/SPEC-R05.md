# SPEC-R05 — Implement business rule BR-005 — Currency handling

- **Scope:** cross_cutting
- **Target entity:** Order
- **Business rules:** BR-005
- **Requirements:** REQ-001, REQ-002, REQ-004

## Current state
All monetary values are expressed using an ISO 4217 currency code; `USD` is the default when the backend omits the field. Money is formatted with that code.

## Target state
Rule BR-005 enforced and covered by automated tests.

## Required changes
- Encode BR-005 in the domain/adapter layer (keep it out of presentational components).
- Required fields: Order.currency.

## Acceptance criteria
- [ ] given currency USD, when totals render, then they use USD currency formatting
- [ ] given a missing currency, when totals render, then USD is assumed

## Evidence
- Target field 'currency' (string) is not represented in the UI.
- BR-005 requires 'currency' but the UI currently has optional_missing (—).
