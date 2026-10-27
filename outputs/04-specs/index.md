# 04 — Change specifications

| Spec | Scope | Title | Rules | Requirements |
| --- | --- | --- | --- | --- |
| SPEC-E01 | entity | Align Order with target contract Order | BR-001, BR-002, BR-003, BR-004, BR-005 | REQ-001, REQ-002, REQ-003, REQ-004 |
| SPEC-E02 | entity | Align OrderItem with target contract OrderLineItem | — | — |
| SPEC-C01 | component | Migrate component OrderList to live contracts | — | — |
| SPEC-X01 | cross_cutting | Align API client layer with target endpoints | — | — |
| SPEC-R01 | cross_cutting | Implement business rule BR-001 — Order grand total reconciliation | BR-001 | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005 |
| SPEC-R02 | cross_cutting | Implement business rule BR-002 — Tax calculation | BR-002 | REQ-004, REQ-005 |
| SPEC-R03 | cross_cutting | Implement business rule BR-003 — Order status transition guard | BR-003 | REQ-001, REQ-002, REQ-003, REQ-004 |
| SPEC-R04 | cross_cutting | Implement business rule BR-004 — Discount eligibility | BR-004 | REQ-001, REQ-002, REQ-004, REQ-005 |
| SPEC-R05 | cross_cutting | Implement business rule BR-005 — Currency handling | BR-005 | REQ-001, REQ-002, REQ-004 |
