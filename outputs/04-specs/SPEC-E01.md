# SPEC-E01 — Align Order with target contract Order

- **Scope:** entity
- **Target entity:** Order
- **Business rules:** BR-001, BR-002, BR-003, BR-004, BR-005
- **Requirements:** REQ-001, REQ-002, REQ-003, REQ-004

## Current state
UI contract `Order` (declared) matched target `Order` with confidence 1.0. 20 finding(s).

## Target state
Implement `Order` exactly as defined in openapi:/components/schemas/Order (9 fields).

## Required changes
- Rename `id` to `orderId` (type stays compatible).
- Introduce an adapter for `customerName` -> `customer`: rename 'customerName' -> 'customer'; UI type 'string' vs target object
- Constrain `status` to the target enum and update badge/select logic: target restricts to enum ['pending', 'paid', 'shipped', 'delivered', 'cancelled']; UI has no union type
- Rename `items` to `lineItems` (type stays compatible).
- Add `amounts: object` (required) and surface it in the UI.
- Add `currency: string` (optional) and surface it in the UI.
- Add `updatedAt: string` (optional) and surface it in the UI.
- Add `placedAt: string` (optional) and surface it in the UI.
- Remove or explicitly remap dummy-only field `customerEmail`.
- Remove or explicitly remap dummy-only field `total`.
- Remove or explicitly remap dummy-only field `discountCode`.
- Remove or explicitly remap dummy-only field `notes`.

## Files in scope
- `/home/user/contract-harness/examples/lovable-app/src/components/OrderList.tsx`
- `/home/user/contract-harness/examples/lovable-app/src/components/OrderStatusBadge.tsx`
- `/home/user/contract-harness/examples/lovable-app/src/components/OrderSummary.tsx`
- `/home/user/contract-harness/examples/lovable-app/src/data/mock-orders.ts`
- `/home/user/contract-harness/examples/lovable-app/src/types/index.ts`

## Acceptance criteria
- [ ] All target enum values are rendered; unknown values fall back safely.
- [ ] BR-001: given a missing amounts object, when the order renders, then a safe placeholder is shown
- [ ] BR-001: given an Order with subtotal, tax and discount, when the summary renders, then total equals subtotal + tax - discount
- [ ] BR-002: given any order, when displayed, then the tax value shown is exactly the value from the contract payload
- [ ] BR-003: given a delivered order, when acting on it, then no transitions are offered
- [ ] BR-003: given a pending order, when acting on it, then only paid and cancelled are offered
- [ ] BR-003: given an unknown status value, when rendering, then a fallback badge is shown without crashing
- [ ] BR-004: given a gold customer, when a discount is applied, then amounts.discount is reflected in the total
- [ ] BR-004: given a silver customer, when an operator tries a discount, then the action is blocked with a rule reference
- [ ] BR-005: given a missing currency, when totals render, then USD is assumed
- [ ] BR-005: given currency USD, when totals render, then they use USD currency formatting
- [ ] Component renders a non-crashing value for `amounts` for empty, loading and populated states.
- [ ] Component renders a non-crashing value for `currency` for empty, loading and populated states.
- [ ] Component renders a non-crashing value for `placedAt` for empty, loading and populated states.
- [ ] Component renders a non-crashing value for `updatedAt` for empty, loading and populated states.
- [ ] No remaining reference to legacy field `id`.
- [ ] No remaining reference to legacy field `items`.
- [ ] Unit test covers conversion `customerName` -> `customer`.

## Evidence
- FIELD_RENAME: rename 'id' -> 'orderId'
- TYPE_MISMATCH: customerName -> customer: rename 'customerName' -> 'customer'; UI type 'string' vs target object
- ENUM_MISMATCH: Mock values ['refunded'] fall outside target enum ['pending', 'paid', 'shipped', 'delivered', 'cancelled'].
- ENUM_NOT_ENFORCED: status -> status: target restricts to enum ['pending', 'paid', 'shipped', 'delivered', 'cancelled']; UI has no union type
- FIELD_RENAME: rename 'items' -> 'lineItems'
- REQUIRED_MISSING: Target field 'amounts' (object) is not represented in the UI.
- OPTIONAL_MISSING: Target field 'currency' (string) is not represented in the UI.
- REQUIRED_NOT_ENFORCED: 'createdAt' is required but mock data contains null/missing values.
- FORMAT_CONSTRAINT: target format constraint: date-time (validate at boundary)
- OPTIONAL_MISSING: Target field 'updatedAt' (string) is not represented in the UI.
- OPTIONAL_MISSING: Target field 'placedAt' (string) is not represented in the UI.
- UI_ONLY_FIELD: 'customerEmail' exists only in UI dummy data and has no target contract field.
- UI_ONLY_FIELD: 'total' exists only in UI dummy data and has no target contract field.
- UI_ONLY_FIELD: 'discountCode' exists only in UI dummy data and has no target contract field.
- UI_ONLY_FIELD: 'notes' exists only in UI dummy data and has no target contract field.
- RULE_FIELD_GAP: BR-001 requires 'amounts' but the UI currently has required_missing (—).
- RULE_FIELD_GAP: BR-002 requires 'amounts' but the UI currently has required_missing (—).
- RULE_FIELD_GAP: BR-003 requires 'status' but the UI currently has enum_not_enforced (status).
- RULE_FIELD_GAP: BR-004 requires 'amounts' but the UI currently has required_missing (—).
- RULE_FIELD_GAP: BR-005 requires 'currency' but the UI currently has optional_missing (—).
