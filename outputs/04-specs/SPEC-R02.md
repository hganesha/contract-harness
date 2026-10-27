# SPEC-R02 — Implement business rule BR-002 — Tax calculation

- **Scope:** cross_cutting
- **Target entity:** Order
- **Business rules:** BR-002
- **Requirements:** REQ-004, REQ-005

## Current state
Tax is computed by the billing service at the prevailing rate on (subtotal minus discount); the UI never calculates tax itself.

## Target state
Rule BR-002 enforced and covered by automated tests.

## Required changes
- Encode BR-002 in the domain/adapter layer (keep it out of presentational components).
- Required fields: Order.amounts.

## Acceptance criteria
- [ ] given any order, when displayed, then the tax value shown is exactly the value from the contract payload

## Evidence
- BR-002 requires 'amounts' but the UI currently has required_missing (—).
