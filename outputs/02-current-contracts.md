# 02 — Current contracts discovered in the UI

## Declared TypeScript contracts (6)
### `OrderItem` — /home/user/contract-harness/examples/lovable-app/src/types/index.ts:2
| Field | Cardinality | TS type | Kind |
| --- | --- | --- | --- |
| id | required | string | primitive |
| name | required | string | primitive |
| price | required | number | primitive |
| qty | required | number | primitive |

### `Order` — /home/user/contract-harness/examples/lovable-app/src/types/index.ts:9
| Field | Cardinality | TS type | Kind |
| --- | --- | --- | --- |
| id | required | string | primitive |
| customerName | required | string | primitive |
| customerEmail | required | string | primitive |
| items | required | OrderItem[] | ref |
| status | required | string | primitive |
| total | required | number | primitive |
| discountCode | optional | string | primitive |
| notes | optional | string | primitive |
| createdAt | required | string | primitive |

### `StatusFilter` (enum) — /home/user/contract-harness/examples/lovable-app/src/types/index.ts:21
Values: `all`, `pending`, `shipped`

### `OrderListProps` — /home/user/contract-harness/examples/lovable-app/src/components/OrderList.tsx:6
| Field | Cardinality | TS type | Kind |
| --- | --- | --- | --- |
| filter | required | StatusFilter | ref |

### `OrderStatusBadgeProps` — /home/user/contract-harness/examples/lovable-app/src/components/OrderStatusBadge.tsx:3
| Field | Cardinality | TS type | Kind |
| --- | --- | --- | --- |
| status | required | Order["status"] | any |

### `OrderSummaryProps` — /home/user/contract-harness/examples/lovable-app/src/components/OrderSummary.tsx:3
| Field | Cardinality | TS type | Kind |
| --- | --- | --- | --- |
| order | required | Order | ref |

## Mock / dummy datasets (1)
### `mockOrders` → inferred entity **Order** — /home/user/contract-harness/examples/lovable-app/src/data/mock-orders.ts
Records: 3; annotation: `Order[]`
| Field | Observed types | Nullable | Present | Samples |
| --- | --- | --- | --- | --- |
| id | string | no | 3/3 | ord-1001, ord-1002, ord-1003 |
| customerName | string | no | 3/3 | Ada Lovelace, Grace Hopper, Alan Turing |
| customerEmail | string | no | 3/3 | ada@example.com, grace@example.com, alan@example.com |
| items | array | no | 3/3 | [{"id": "i-1", "name": "Mechanical keyboard", "…, [{"id": "i-3", "name": "Compiler science mug", …, [{"id": "i-4", "name": "Enigma puzzle set", "pr… |
| status | string | no | 3/3 | pending, refunded, shipped |
| total | number | no | 3/3 | 139.99, 55.5, 48.71 |
| discountCode | string | yes | 1/3 | SAVE10 |
| notes | string, null | yes | 2/3 | Leave at front desk |
| createdAt | string | yes | 2/3 | 2026-10-01T14:22:00Z, 2026-10-18T09:05:00Z |

## Data-access call sites (2)
| Client | Method | Target | Location |
| --- | --- | --- | --- |
| supabase | SELECT | orders | /home/user/contract-harness/examples/lovable-app/src/lib/api.ts:12 |
| supabase | UPDATE | orders | /home/user/contract-harness/examples/lovable-app/src/lib/api.ts:17 |

## Components & pages (4)
| Component | Contracts | Mock data | API calls | Data fields touched |
| --- | --- | --- | --- | --- |
| OrderList | OrderListProps, StatusFilter | mockOrders | — | 10 |
| OrderStatusBadge | Order, OrderStatusBadgeProps | — | — | 0 |
| OrderSummary | Order, OrderSummaryProps | — | — | 5 |
| OrdersPage | StatusFilter | — | — | 0 |
