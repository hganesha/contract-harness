"""Extract declared TS contracts: ``interface``, ``type`` and ``enum``.

This is a heuristic scanner rather than a full TypeScript compiler, but it is
bracket/quote aware, so generics, unions and inline nested objects are handled
well enough for contract alignment. Every result keeps ``source_file`` +
``line`` so findings can point developers at exact code.
"""
from __future__ import annotations

import re

from ..models import UIContract, UIField
from ..utils import line_of, match_bracket, read_text, split_top_level, strip_comments

_PRIMITIVES = {"string", "number", "boolean", "unknown", "any", "void", "null", "undefined", "Date"}
_INTERFACE_RE = re.compile(r"(?:export\s+)?interface\s+([A-Za-z_$][\w$]*)\b[^{]*\{")
_TYPE_RE = re.compile(r"(?:export\s+)?type\s+([A-Za-z_$][\w$]*)\s*=\s*")
_ENUM_RE = re.compile(r"(?:export\s+)?enum\s+([A-Za-z_$][\w$]*)\s*\{")
_FIELD_RE = re.compile(r"^([A-Za-z_$][\w$]*)\s*(\?)?\s*:\s*(.+?)\s*$", re.DOTALL)
_LITERAL_UNION_RE = re.compile(r"^[\s\w'\"|]+$")


def _classify_type(raw: str) -> tuple[str, str, list[str], bool]:
    """Return (kind, ref, enum_values, is_array) for a raw TS type string."""
    t = raw.strip().rstrip(";").strip()

    is_array = bool(re.search(r"\[\]$", t)) or bool(re.match(r"^Array<", t))
    inner = re.sub(r"\[\]$", "", t)
    m = re.match(r"^Array<(.+)>$", inner)
    if m:
        inner = m.group(1)

    if inner.startswith("{"):
        return "object", "", [], is_array

    literals = re.findall(r"['\"]([^'\"]+)['\"]", inner)
    if literals and "|" in inner:
        return "enum", "", literals, is_array

    inner_clean = re.sub(r"<.*>", "", inner).strip()
    if inner_clean in _PRIMITIVES:
        return "primitive", "", [], is_array
    if "|" in inner:
        # union of named refs / primitives
        return "union", inner_clean, [], is_array
    if re.match(r"^[A-Z][\w$]*$", inner_clean):
        return "ref", inner_clean, [], is_array
    return "any", "", [], is_array


def _parse_field_body(body: str, source_file: str, base_line: int) -> list[UIField]:
    fields: list[UIField] = []
    for chunk in split_top_level(body, ";\n"):
        line = chunk.strip()
        if not line:
            continue
        m = _FIELD_RE.match(line)
        if not m:
            continue
        name, optional, raw_type = m.group(1), m.group(2), m.group(3).strip()
        kind, ref, enum, is_array = _classify_type(raw_type)
        children: list[UIField] = []
        if kind == "object":
            open_idx = raw_type.find("{")
            if open_idx >= 0:
                close = match_bracket(raw_type, open_idx)
                if close > open_idx:
                    children = _parse_field_body(raw_type[open_idx + 1:close], source_file, base_line)
        type_label = raw_type + ("[]" if is_array and not raw_type.endswith("[]") else "")
        fields.append(
            UIField(
                name=name,
                type_raw=type_label,
                kind=kind,
                required=optional is None,
                enum=enum,
                ref=ref,
                children=children,
                source_file=source_file,
                line=base_line,
            )
        )
    return fields


def extract_contracts(file_path: str) -> list[UIContract]:
    text = strip_comments(read_text(file_path))
    contracts: list[UIContract] = []
    consumed_spans: list[tuple[int, int]] = []

    # interfaces -----------------------------------------------------------
    for m in _INTERFACE_RE.finditer(text):
        open_idx = text.find("{", m.start())
        close = match_bracket(text, open_idx)
        if close == -1:
            continue
        consumed_spans.append((m.start(), close))
        body = text[open_idx + 1:close]
        contracts.append(
            UIContract(
                name=m.group(1),
                kind="interface",
                fields=_parse_field_body(body, file_path, line_of(text, m.start())),
                source_file=file_path,
                line=line_of(text, m.start()),
            )
        )

    # enums ----------------------------------------------------------------
    for m in _ENUM_RE.finditer(text):
        if any(s <= m.start() <= e for s, e in consumed_spans):
            continue
        open_idx = text.find("{", m.start())
        close = match_bracket(text, open_idx)
        if close == -1:
            continue
        values: list[str] = []
        for member in text[open_idx + 1:close].split(","):
            member = member.strip()
            if not member:
                continue
            lit = re.search(r"=\s*['\"]([^'\"]+)['\"]", member)
            values.append(lit.group(1) if lit else member.split("=")[0].strip())
        contracts.append(
            UIContract(
                name=m.group(1),
                kind="enum",
                enum_values=values,
                source_file=file_path,
                line=line_of(text, m.start()),
            )
        )

    # type aliases ----------------------------------------------------------
    for m in _TYPE_RE.finditer(text):
        if any(s <= m.start() <= e for s, e in consumed_spans):
            continue
        rest = text[m.end():]
        if rest.lstrip().startswith("{"):
            open_idx = m.end() + rest.index("{")
            close = match_bracket(text, open_idx)
            if close == -1:
                continue
            body = text[open_idx + 1:close]
            contracts.append(
                UIContract(
                    name=m.group(1),
                    kind="type",
                    fields=_parse_field_body(body, file_path, line_of(text, m.start())),
                    source_file=file_path,
                    line=line_of(text, m.start()),
                )
            )
            continue
        # alias up to ; or newline
        end_m = re.search(r";|\n", rest)
        alias = rest[: end_m.start()].strip() if end_m else rest.strip()
        kind, _ref, enum, _arr = _classify_type(alias)
        contracts.append(
            UIContract(
                name=m.group(1),
                kind="enum" if kind == "enum" else "type",
                enum_values=enum,
                source_file=file_path,
                line=line_of(text, m.start()),
            )
        )
    return contracts


def extract_all_contracts(files: list[str]) -> list[UIContract]:
    out: list[UIContract] = []
    for f in files:
        out.extend(extract_contracts(f))
    return out
