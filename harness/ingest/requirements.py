"""Parse a requirements Markdown file.

Supported heading patterns (anything matching ``REQ-###`` is picked up)::

    ## REQ-001 — View order list
    ### REQ-002: Order detail drill-down

Acceptance criteria are bullet lines starting with ``- [ ]`` / ``- [x]``.
"""
from __future__ import annotations

import re

from ..models import Requirement
from ..utils import read_text

_REQ_HEADING = re.compile(r"^#{1,4}\s+(REQ-\d+)\s*[:\-–—]*\s*(.*)$", re.MULTILINE)
_AC = re.compile(r"^\s*[-*]\s*\[[ xX]\]\s*(.+)$", re.MULTILINE)


def parse_requirements(path: str) -> list[Requirement]:
    text = read_text(path)
    matches = list(_REQ_HEADING.finditer(text))
    requirements: list[Requirement] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        acceptance = [am.group(1).strip() for am in _AC.finditer(body)]
        requirements.append(
            Requirement(
                id=m.group(1),
                title=m.group(2).strip(),
                body=body,
                acceptance=acceptance,
                source_file=path,
            )
        )
    return requirements
