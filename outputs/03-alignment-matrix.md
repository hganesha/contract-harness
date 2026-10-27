# 03 — Contract alignment matrix

Finding counts: 🔴 high **12**, 🔵 info **1**, 🟡 low **5**, 🟠 medium **10**

## `Order` → **Order** (confidence 1.0)
| UI field | UI type | Target field | Target type | Target req. | Status | Note |
| --- | --- | --- | --- | --- | --- | --- |
| id | string | orderId | string | required | FIELD_RENAME | rename 'id' -> 'orderId' |
| customerName | string | customer | object | required | TYPE_MISMATCH | rename 'customerName' -> 'customer'; UI type 'string' vs target object |
| status | string | status | string | required | ENUM_NOT_ENFORCED | target restricts to enum ['pending', 'paid', 'shipped', 'delivered', 'cancelled']; UI has no union type |
| items | OrderItem[] | lineItems | object[] | required | FIELD_RENAME | rename 'items' -> 'lineItems' |
| — | — | amounts | object | required | REQUIRED_MISSING | not represented anywhere in the UI contract |
| — | — | currency | string | optional | OPTIONAL_MISSING | not represented anywhere in the UI contract |
| createdAt | string | createdAt | string | required | MATCH | target format constraint: date-time (validate at boundary) |
| — | — | updatedAt | string | optional | OPTIONAL_MISSING | not represented anywhere in the UI contract |
| — | — | placedAt | string | optional | OPTIONAL_MISSING | not represented anywhere in the UI contract |
| customerEmail | string | — | — | optional | UI_ONLY_FIELD | dummy-only field: remove or map explicitly |
| total | number | — | — | optional | UI_ONLY_FIELD | dummy-only field: remove or map explicitly |
| discountCode | string | — | — | optional | UI_ONLY_FIELD | dummy-only field: remove or map explicitly |
| notes | string | — | — | optional | UI_ONLY_FIELD | dummy-only field: remove or map explicitly |

**Findings**
- 🟠 medium `FIELD_RENAME` — **orderId**: rename 'id' -> 'orderId'
  - evidence: `/home/user/contract-harness/examples/lovable-app/src/types/index.ts:9`
- 🔴 high `TYPE_MISMATCH` — **customer**: customerName -> customer: rename 'customerName' -> 'customer'; UI type 'string' vs target object
  - evidence: `mock data in 3 records; samples=['Ada Lovelace', 'Grace Hopper', 'Alan Turing']; nullable=False`
  - evidence: `/home/user/contract-harness/examples/lovable-app/src/types/index.ts:9`
- 🔴 high `ENUM_MISMATCH` — **status**: Mock values ['refunded'] fall outside target enum ['pending', 'paid', 'shipped', 'delivered', 'cancelled'].
  - evidence: `mock data in 3 records; samples=['pending', 'refunded', 'shipped']; nullable=False`
  - evidence: `observed on field 'status'`
- 🟠 medium `ENUM_NOT_ENFORCED` — **status**: status -> status: target restricts to enum ['pending', 'paid', 'shipped', 'delivered', 'cancelled']; UI has no union type
  - evidence: `mock data in 3 records; samples=['pending', 'refunded', 'shipped']; nullable=False`
  - evidence: `/home/user/contract-harness/examples/lovable-app/src/types/index.ts:9`
- 🟠 medium `FIELD_RENAME` — **lineItems**: rename 'items' -> 'lineItems'
  - evidence: `/home/user/contract-harness/examples/lovable-app/src/types/index.ts:9`
- 🔴 high `REQUIRED_MISSING` — **amounts**: Target field 'amounts' (object) is not represented in the UI.
- 🟠 medium `OPTIONAL_MISSING` — **currency**: Target field 'currency' (string) is not represented in the UI.
- 🟠 medium `REQUIRED_NOT_ENFORCED` — **createdAt**: 'createdAt' is required but mock data contains null/missing values.
  - evidence: `mock data in 3 records; samples=['2026-10-01T14:22:00Z', '2026-10-18T09:05:00Z']; nullable=True`
- 🔵 info `FORMAT_CONSTRAINT` — **createdAt**: target format constraint: date-time (validate at boundary)
  - evidence: `mock data in 3 records; samples=['2026-10-01T14:22:00Z', '2026-10-18T09:05:00Z']; nullable=True`
- 🟠 medium `OPTIONAL_MISSING` — **updatedAt**: Target field 'updatedAt' (string) is not represented in the UI.
- 🟠 medium `OPTIONAL_MISSING` — **placedAt**: Target field 'placedAt' (string) is not represented in the UI.
- 🟡 low `UI_ONLY_FIELD` — **customerEmail**: 'customerEmail' exists only in UI dummy data and has no target contract field.
  - evidence: `/home/user/contract-harness/examples/lovable-app/src/types/index.ts:9`
- 🟡 low `UI_ONLY_FIELD` — **total**: 'total' exists only in UI dummy data and has no target contract field.
  - evidence: `/home/user/contract-harness/examples/lovable-app/src/types/index.ts:9`
- 🟡 low `UI_ONLY_FIELD` — **discountCode**: 'discountCode' exists only in UI dummy data and has no target contract field.
  - evidence: `/home/user/contract-harness/examples/lovable-app/src/types/index.ts:9`
- 🟡 low `UI_ONLY_FIELD` — **notes**: 'notes' exists only in UI dummy data and has no target contract field.
  - evidence: `/home/user/contract-harness/examples/lovable-app/src/types/index.ts:9`
- 🔴 high `RULE_FIELD_GAP` — **amounts**: BR-001 requires 'amounts' but the UI currently has required_missing (—).
  - evidence: `rule: Order grand total reconciliation`
- 🔴 high `RULE_FIELD_GAP` — **amounts**: BR-002 requires 'amounts' but the UI currently has required_missing (—).
  - evidence: `rule: Tax calculation`
- 🔴 high `RULE_FIELD_GAP` — **status**: BR-003 requires 'status' but the UI currently has enum_not_enforced (status).
  - evidence: `rule: Order status transition guard`
- 🔴 high `RULE_FIELD_GAP` — **amounts**: BR-004 requires 'amounts' but the UI currently has required_missing (—).
  - evidence: `rule: Discount eligibility`
- 🔴 high `RULE_FIELD_GAP` — **currency**: BR-005 requires 'currency' but the UI currently has optional_missing (—).
  - evidence: `rule: Currency handling`

## `OrderItem` → **OrderLineItem** (confidence 0.82)
| UI field | UI type | Target field | Target type | Target req. | Status | Note |
| --- | --- | --- | --- | --- | --- | --- |
| id | string | lineId | string | required | FIELD_RENAME | rename 'id' -> 'lineId' |
| — | — | productId | string | required | REQUIRED_MISSING | not represented anywhere in the UI contract |
| — | — | sku | string | required | REQUIRED_MISSING | not represented anywhere in the UI contract |
| qty | number | quantity | integer | required | FIELD_RENAME | rename 'qty' -> 'quantity' |
| price | number | unitPrice | number | required | FIELD_RENAME | rename 'price' -> 'unitPrice' |
| — | — | lineTotal | number | required | REQUIRED_MISSING | not represented anywhere in the UI contract |
| name | string | — | — | optional | UI_ONLY_FIELD | dummy-only field: remove or map explicitly |

**Findings**
- 🟠 medium `FIELD_RENAME` — **lineId**: rename 'id' -> 'lineId'
  - evidence: `/home/user/contract-harness/examples/lovable-app/src/types/index.ts:2`
- 🔴 high `REQUIRED_MISSING` — **productId**: Target field 'productId' (string) is not represented in the UI.
- 🔴 high `REQUIRED_MISSING` — **sku**: Target field 'sku' (string) is not represented in the UI.
- 🟠 medium `FIELD_RENAME` — **quantity**: rename 'qty' -> 'quantity'
  - evidence: `/home/user/contract-harness/examples/lovable-app/src/types/index.ts:2`
- 🟠 medium `FIELD_RENAME` — **unitPrice**: rename 'price' -> 'unitPrice'
  - evidence: `/home/user/contract-harness/examples/lovable-app/src/types/index.ts:2`
- 🔴 high `REQUIRED_MISSING` — **lineTotal**: Target field 'lineTotal' (number) is not represented in the UI.
- 🟡 low `UI_ONLY_FIELD` — **name**: 'name' exists only in UI dummy data and has no target contract field.
  - evidence: `/home/user/contract-harness/examples/lovable-app/src/types/index.ts:2`

## Unmatched
- UI contracts without a target: StatusFilter, OrderListProps, OrderStatusBadgeProps, OrderSummaryProps
- Target entities without UI representation: Customer, OrderAmounts
