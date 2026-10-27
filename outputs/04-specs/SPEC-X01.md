# SPEC-X01 — Align API client layer with target endpoints

- **Scope:** cross_cutting

## Current state
Detected 2 call site(s); 4 target endpoint(s).

## Target state
Typed client functions covering every target endpoint with contract-validated IO.

## Required changes
- Add typed client call for GET /orders (entity: Order).
- Add typed client call for POST /orders (entity: Order).
- Add typed client call for GET /orders/{orderId} (entity: Order).
- Add typed client call for PATCH /orders/{orderId}/status (entity: Order).

## Files in scope
- `/home/user/contract-harness/examples/lovable-app/src/lib/api.ts`

## Acceptance criteria
- [ ] Each target endpoint has exactly one typed client function.
- [ ] Runtime schema validation (zod/valibot or equivalent) on every response.
