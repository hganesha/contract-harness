# 06 — Traceability matrix

## Business rules → contracts → specs → tasks

| Rule | Title | Entities | Required fields | Gap analysis | Specs | Tasks |
| --- | --- | --- | --- | --- | --- | --- |
| BR-001 | Order grand total reconciliation | Order | Order.amounts | 2 finding(s) | SPEC-E01, SPEC-R01 | T-009 |
| BR-002 | Tax calculation | Order | Order.amounts | 1 finding(s) | SPEC-E01, SPEC-R02 | T-010 |
| BR-003 | Order status transition guard | Order | Order.status | 3 finding(s) | SPEC-E01, SPEC-R03 | T-011 |
| BR-004 | Discount eligibility | Order, Customer | Order.amounts, Customer.tier | 2 finding(s) | SPEC-E01, SPEC-R04 | T-012 |
| BR-005 | Currency handling | Order | Order.currency | 2 finding(s) | SPEC-E01, SPEC-R05 | T-013 |

## Requirements → affected entities → specs
| Requirement | Title | Entities | Specs |
| --- | --- | --- | --- |
| REQ-001 | View the order list | Customer, Order | SPEC-E01, SPEC-R01, SPEC-R03, SPEC-R04, SPEC-R05 |
| REQ-002 | Inspect an order's detail | Customer, Order | SPEC-E01, SPEC-R01, SPEC-R03, SPEC-R04, SPEC-R05 |
| REQ-003 | Manage the order status workflow | Order | SPEC-E01, SPEC-R01, SPEC-R03 |
| REQ-004 | Display the money breakdown including tax | Order | SPEC-E01, SPEC-R01, SPEC-R02, SPEC-R03, SPEC-R04, SPEC-R05 |
| REQ-005 | Apply discount eligibility for premium customers | Customer | SPEC-R01, SPEC-R02, SPEC-R04 |
