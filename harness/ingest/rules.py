"""Parse business rules from Markdown (preferred) or JSON.

Markdown convention::

    ### BR-001 — Order totals must include tax
    Description text...
    - Applies to: Order, OrderLineItem
    - Requires fields: Order.amounts.tax, Order.status
    - Acceptance:
      - given ... when ... then ...

JSON convention: a list of objects with the same keys as ``BusinessRule``.
"""
from __future__ import annotations

import json
import re

from ..models import BusinessRule
from ..utils import read_text

_RULE_HEADING = re.compile(r"^#{1,4}\s+(BR-\d+)\s*[:\-–—]*\s*(.*)$", re.MULTILINE)
_LIST_LINE = re.compile(r"^\s*[-*]\s+(.+)$", re.MULTILINE)


def _split_list(raw: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,;]", raw) if part.strip()]


def parse_rules_markdown(path: str) -> list[BusinessRule]:
    text = read_text(path)
    matches = list(_RULE_HEADING.finditer(text))
    rules: list[BusinessRule] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]

        applies_to: list[str] = []
        requires_fields: list[str] = []
        acceptance: list[str] = []
        description_parts: list[str] = []

        for line in body.splitlines():
            stripped = line.strip()
            low = stripped.lower()
            if low.startswith(("- applies to:", "* applies to:")):
                applies_to = _split_list(stripped.split(":", 1)[1])
            elif low.startswith(("- requires fields:", "* requires fields:",
                                 "- required fields:", "* required fields:")):
                requires_fields = _split_list(stripped.split(":", 1)[1])
            elif low.startswith(("- acceptance:", "* acceptance:")):
                continue
            elif re.match(r"^\s*[-*]\s+", stripped):
                # bullets after an "Acceptance" label are acceptance criteria
                acceptance.append(_LIST_LINE.match(stripped).group(1).strip())
            elif stripped:
                description_parts.append(stripped)

        rules.append(
            BusinessRule(
                id=m.group(1),
                title=m.group(2).strip(),
                description=" ".join(description_parts),
                applies_to=applies_to,
                requires_fields=requires_fields,
                acceptance=acceptance,
                source_file=path,
            )
        )
    return rules


def parse_rules_json(path: str) -> list[BusinessRule]:
    payload = json.loads(read_text(path))
    if isinstance(payload, dict):
        payload = payload.get("rules", [])
    return [
        BusinessRule(
            id=r["id"],
            title=r.get("title", ""),
            description=r.get("description", ""),
            applies_to=r.get("applies_to", []),
            requires_fields=r.get("requires_fields", []),
            acceptance=r.get("acceptance", []),
            source_file=path,
        )
        for r in payload
    ]


def parse_rules(path: str) -> list[BusinessRule]:
    if path.endswith(".json"):
        return parse_rules_json(path)
    return parse_rules_markdown(path)
