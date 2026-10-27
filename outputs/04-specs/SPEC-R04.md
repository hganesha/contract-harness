# SPEC-R04 — Implement business rule BR-004 — Discount eligibility

- **Scope:** cross_cutting
- **Target entity:** Order, Customer
- **Business rules:** BR-004
- **Requirements:** REQ-001, REQ-002, REQ-004, REQ-005

## Current state
A discount may be applied only when the linked customer's tier is `gold` or `platinum`; silver and bronze customers are ineligible.

## Target state
Rule BR-004 enforced and covered by automated tests.

## Required changes
- Encode BR-004 in the domain/adapter layer (keep it out of presentational components).
- Required fields: Order.amounts, Customer.tier.

## Acceptance criteria
- [ ] given a silver customer, when an operator tries a discount, then the action is blocked with a rule reference
- [ ] given a gold customer, when a discount is applied, then amounts.discount is reflected in the total

## Evidence
- BR-004 requires 'amounts' but the UI currently has required_missing (—).
- BR-004 applies to 'Customer', which has no matching UI contract or mock data yet.
