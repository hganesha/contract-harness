# SPEC-R03 — Implement business rule BR-003 — Order status transition guard

- **Scope:** cross_cutting
- **Target entity:** Order
- **Business rules:** BR-003
- **Requirements:** REQ-001, REQ-002, REQ-003, REQ-004

## Current state
Allowed transitions are pending -> paid -> shipped -> delivered. An order may be cancelled only from pending or paid. Any other transition is rejected.

## Target state
Rule BR-003 enforced and covered by automated tests.

## Required changes
- Encode BR-003 in the domain/adapter layer (keep it out of presentational components).
- Required fields: Order.status.

## Acceptance criteria
- [ ] given a pending order, when acting on it, then only paid and cancelled are offered
- [ ] given a delivered order, when acting on it, then no transitions are offered
- [ ] given an unknown status value, when rendering, then a fallback badge is shown without crashing

## Evidence
- Mock values ['refunded'] fall outside target enum ['pending', 'paid', 'shipped', 'delivered', 'cancelled'].
- status -> status: target restricts to enum ['pending', 'paid', 'shipped', 'delivered', 'cancelled']; UI has no union type
- BR-003 requires 'status' but the UI currently has enum_not_enforced (status).
