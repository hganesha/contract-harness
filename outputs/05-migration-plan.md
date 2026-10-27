# 05 — Migration plan

## Executive summary

- 15 tasks across 7 phases
- 9 change specs; findings: high=12, info=1, low=5, medium=10
- Effort: S=6, M=6, L=3

## Phase 01-contract-freeze

### T-001 — Snapshot target contracts and scaffold contract tests  `effort:S` `risk:S`
Vendor the target schemas (OpenAPI/JSON) into the repo and generate TypeScript types plus response validators so every later phase has a single source of truth.
- **Files:** `src/contracts/ (new)`, `tests/contract/ (new)`
- **Refs:** SPEC-X01
- **Acceptance:**
  - [ ] Generated types compile with no errors.
  - [ ] A sample fixture fails validation when intentionally corrupted.

## Phase 02-types-and-adapters

### T-002 — Rebuild Order types and add a mock→contract adapter  `effort:L` `risk:L`
Replace the UI's Order shape with the target Order contract and centralize field renames, type coercions and enum mapping in one adapter function so components stay declarative.
- **Depends on:** T-001
- **Files:** `/home/user/contract-harness/examples/lovable-app/src/components/OrderList.tsx`, `/home/user/contract-harness/examples/lovable-app/src/components/OrderStatusBadge.tsx`, `/home/user/contract-harness/examples/lovable-app/src/components/OrderSummary.tsx`, `/home/user/contract-harness/examples/lovable-app/src/data/mock-orders.ts`, `/home/user/contract-harness/examples/lovable-app/src/types/index.ts`
- **Refs:** SPEC-E01
- **Acceptance:**
  - [ ] Adapter maps every legacy Order field to Order (exhaustive switch).
  - [ ] Adapter unit tests cover nulls, unknown enum values and missing optional fields.

### T-003 — Rebuild OrderLineItem types and add a mock→contract adapter  `effort:L` `risk:L`
Replace the UI's OrderItem shape with the target OrderLineItem contract and centralize field renames, type coercions and enum mapping in one adapter function so components stay declarative.
- **Depends on:** T-001
- **Files:** `/home/user/contract-harness/examples/lovable-app/src/components/OrderList.tsx`, `/home/user/contract-harness/examples/lovable-app/src/components/OrderSummary.tsx`, `/home/user/contract-harness/examples/lovable-app/src/types/index.ts`
- **Refs:** SPEC-E02
- **Acceptance:**
  - [ ] Adapter maps every legacy OrderItem field to OrderLineItem (exhaustive switch).
  - [ ] Adapter unit tests cover nulls, unknown enum values and missing optional fields.

## Phase 03-api-client

### T-004 — Add typed client for GET /orders  `effort:S` `risk:S`
Create one typed client function with runtime response validation; wire query keys/caching consistent with the existing data layer.
- **Depends on:** T-001, T-002
- **Files:** `/home/user/contract-harness/examples/lovable-app/src/lib/api.ts`
- **Refs:** SPEC-X01
- **Acceptance:**
  - [ ] Calling listOrders returns a validated Order type.
  - [ ] Network and validation errors surface through a typed error channel.

### T-005 — Add typed client for POST /orders  `effort:S` `risk:S`
Create one typed client function with runtime response validation; wire query keys/caching consistent with the existing data layer.
- **Depends on:** T-001, T-002
- **Files:** `/home/user/contract-harness/examples/lovable-app/src/lib/api.ts`
- **Refs:** SPEC-X01
- **Acceptance:**
  - [ ] Calling createOrder returns a validated Order type.
  - [ ] Network and validation errors surface through a typed error channel.

### T-006 — Add typed client for GET /orders/{orderId}  `effort:S` `risk:S`
Create one typed client function with runtime response validation; wire query keys/caching consistent with the existing data layer.
- **Depends on:** T-001, T-002
- **Files:** `/home/user/contract-harness/examples/lovable-app/src/lib/api.ts`
- **Refs:** SPEC-X01
- **Acceptance:**
  - [ ] Calling getOrder returns a validated Order type.
  - [ ] Network and validation errors surface through a typed error channel.

### T-007 — Add typed client for PATCH /orders/{orderId}/status  `effort:S` `risk:S`
Create one typed client function with runtime response validation; wire query keys/caching consistent with the existing data layer.
- **Depends on:** T-001, T-002
- **Files:** `/home/user/contract-harness/examples/lovable-app/src/lib/api.ts`
- **Refs:** SPEC-X01
- **Acceptance:**
  - [ ] Calling updateOrderStatus returns a validated Order type.
  - [ ] Network and validation errors surface through a typed error channel.

## Phase 04-component-migration

### T-008 — Migrate OrderList to live data and target field names  `effort:L` `risk:M`
Remove mock import(s) mockOrders and source data from the real API client / query hook instead.; Update field access `id` -> `orderId` on Order (FIELD_RENAME).; Update field access `id` -> `lineId` on OrderLineItem (FIELD_RENAME). …
- **Depends on:** T-002, T-003, T-005, T-006, T-007
- **Files:** `/home/user/contract-harness/examples/lovable-app/src/components/OrderList.tsx`
- **Refs:** SPEC-C01
- **Acceptance:**
  - [ ] Renders against a real-contract fixture without dummy imports.
  - [ ] Loading, error and empty states verified.

## Phase 05-business-rules

### T-009 — Enforce BR-001 in the domain layer  `effort:M` `risk:L`
The order grand total must equal subtotal plus tax minus discount. The UI must render the server-computed amounts rather than recomputing them client-side.
- **Depends on:** T-002
- **Refs:** SPEC-R01, BR-001
- **Acceptance:**
  - [ ] given an Order with subtotal, tax and discount, when the summary renders, then total equals subtotal + tax - discount
  - [ ] given a missing amounts object, when the order renders, then a safe placeholder is shown

### T-010 — Enforce BR-002 in the domain layer  `effort:M` `risk:L`
Tax is computed by the billing service at the prevailing rate on (subtotal minus discount); the UI never calculates tax itself.
- **Depends on:** T-002
- **Refs:** SPEC-R02, BR-002
- **Acceptance:**
  - [ ] given any order, when displayed, then the tax value shown is exactly the value from the contract payload

### T-011 — Enforce BR-003 in the domain layer  `effort:M` `risk:L`
Allowed transitions are pending -> paid -> shipped -> delivered. An order may be cancelled only from pending or paid. Any other transition is rejected.
- **Depends on:** T-002
- **Refs:** SPEC-R03, BR-003
- **Acceptance:**
  - [ ] given a pending order, when acting on it, then only paid and cancelled are offered
  - [ ] given a delivered order, when acting on it, then no transitions are offered
  - [ ] given an unknown status value, when rendering, then a fallback badge is shown without crashing

### T-012 — Enforce BR-004 in the domain layer  `effort:M` `risk:L`
A discount may be applied only when the linked customer's tier is `gold` or `platinum`; silver and bronze customers are ineligible.
- **Depends on:** T-002
- **Refs:** SPEC-R04, BR-004
- **Acceptance:**
  - [ ] given a silver customer, when an operator tries a discount, then the action is blocked with a rule reference
  - [ ] given a gold customer, when a discount is applied, then amounts.discount is reflected in the total

### T-013 — Enforce BR-005 in the domain layer  `effort:M` `risk:L`
All monetary values are expressed using an ISO 4217 currency code; `USD` is the default when the backend omits the field. Money is formatted with that code.
- **Depends on:** T-002
- **Refs:** SPEC-R05, BR-005
- **Acceptance:**
  - [ ] given currency USD, when totals render, then they use USD currency formatting
  - [ ] given a missing currency, when totals render, then USD is assumed

## Phase 06-cleanup

### T-014 — Delete dummy data module /home/user/contract-harness/examples/lovable-app/src/data/mock-orders.ts  `effort:S` `risk:S`
Remove the mock module and any re-exports once every consuming component reads live data. Search the repo for the const names to confirm zero references.
- **Depends on:** T-008
- **Files:** `/home/user/contract-harness/examples/lovable-app/src/data/mock-orders.ts`
- **Refs:** SPEC-E01
- **Acceptance:**
  - [ ] No import of /home/user/contract-harness/examples/lovable-app/src/data/mock-orders.ts remains; production build succeeds.

## Phase 07-verification

### T-015 — Contract, rule and visual verification  `effort:M` `risk:S`
Run the full verification sweep: contract tests against recorded fixtures, business-rule tests with violation cases, and visual QA of loading/empty/error states on every migrated screen.
- **Depends on:** T-008, T-009, T-010, T-011, T-012, T-013, T-014
- **Refs:** SPEC-E01, SPEC-E02, SPEC-C01, SPEC-X01, SPEC-R01, SPEC-R02, SPEC-R03, SPEC-R04, SPEC-R05
- **Acceptance:**
  - [ ] All contract tests pass against target fixtures.
  - [ ] Every business rule has at least one happy-path and one violation test.
  - [ ] No dummy data references remain in the codebase.
  - [ ] Migrated screens verified for loading, empty and error states.
