# SPEC-E02 — Align OrderItem with target contract OrderLineItem

- **Scope:** entity
- **Target entity:** OrderLineItem

## Current state
UI contract `OrderItem` (declared) matched target `OrderLineItem` with confidence 0.82. 7 finding(s).

## Target state
Implement `OrderLineItem` exactly as defined in openapi:/components/schemas/OrderLineItem (6 fields).

## Required changes
- Rename `id` to `lineId` (type stays compatible).
- Add `productId: string` (required) and surface it in the UI.
- Add `sku: string` (required) and surface it in the UI.
- Rename `qty` to `quantity` (type stays compatible).
- Rename `price` to `unitPrice` (type stays compatible).
- Add `lineTotal: number` (required) and surface it in the UI.
- Remove or explicitly remap dummy-only field `name`.

## Files in scope
- `/home/user/contract-harness/examples/lovable-app/src/components/OrderList.tsx`
- `/home/user/contract-harness/examples/lovable-app/src/components/OrderSummary.tsx`
- `/home/user/contract-harness/examples/lovable-app/src/types/index.ts`

## Acceptance criteria
- [ ] Component renders a non-crashing value for `lineTotal` for empty, loading and populated states.
- [ ] Component renders a non-crashing value for `productId` for empty, loading and populated states.
- [ ] Component renders a non-crashing value for `sku` for empty, loading and populated states.
- [ ] No remaining reference to legacy field `id`.
- [ ] No remaining reference to legacy field `price`.
- [ ] No remaining reference to legacy field `qty`.

## Evidence
- FIELD_RENAME: rename 'id' -> 'lineId'
- REQUIRED_MISSING: Target field 'productId' (string) is not represented in the UI.
- REQUIRED_MISSING: Target field 'sku' (string) is not represented in the UI.
- FIELD_RENAME: rename 'qty' -> 'quantity'
- FIELD_RENAME: rename 'price' -> 'unitPrice'
- REQUIRED_MISSING: Target field 'lineTotal' (number) is not represented in the UI.
- UI_ONLY_FIELD: 'name' exists only in UI dummy data and has no target contract field.
