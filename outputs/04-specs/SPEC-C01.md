# SPEC-C01 — Migrate component OrderList to live contracts

- **Scope:** component

## Current state
OrderList uses mock data=['mockOrders'], api=none, contracts=['OrderListProps', 'StatusFilter'].

## Target state
Component is presentational; data arrives via typed query hooks.

## Required changes
- Remove mock import(s) mockOrders and source data from the real API client / query hook instead.
- Update field access `id` -> `orderId` on Order (FIELD_RENAME).
- Update field access `id` -> `lineId` on OrderLineItem (FIELD_RENAME).
- Update field access `customerName` -> `customer` on Order (TYPE_MISMATCH).
- Update field access `items` -> `lineItems` on Order (FIELD_RENAME).
- Update field access `qty` -> `quantity` on OrderLineItem (FIELD_RENAME).
- Update field access `price` -> `unitPrice` on OrderLineItem (FIELD_RENAME).
- Add loading, error and empty states (mock data never exercises them).

## Files in scope
- `/home/user/contract-harness/examples/lovable-app/src/components/OrderList.tsx`

## Acceptance criteria
- [ ] Renders against a real-contract fixture without dummy imports.
- [ ] Loading, error and empty states verified.

## Evidence
- props: filter
