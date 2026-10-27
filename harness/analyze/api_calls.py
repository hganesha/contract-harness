"""Detect how the UI currently reaches for data: fetch, axios, Supabase, RQ."""
from __future__ import annotations

import re

from ..models import APICall
from ..utils import line_of, read_text, strip_comments

_FETCH_RE = re.compile(r"fetch\s*\(\s*[`'\"]([^`'\"]+)[`'\"]")
_METHOD_RE = re.compile(r"method\s*:\s*['\"]([A-Z]+)['\"]")
_AXIOS_RE = re.compile(r"axios\.(get|post|put|patch|delete)\s*\(\s*[`'\"]([^`'\"]+)[`'\"]")
_SUPA_RE = re.compile(r"\.from\(\s*['\"]([\w.-]+)['\"]\s*\)([^;]{0,120})")
_RQ_RE = re.compile(r"use(Query|Mutation)\s*\(")
_QUERY_KEY_RE = re.compile(r"queryKey\s*:\s*\[([^\]]{0,120})\]")


def scan_api_calls(files: list[str]) -> list[APICall]:
    calls: list[APICall] = []
    for path in files:
        text = strip_comments(read_text(path))
        for m in _FETCH_RE.finditer(text):
            window = text[m.start():m.start() + 240]
            method_m = _METHOD_RE.search(window)
            calls.append(
                APICall(
                    file=path,
                    line=line_of(text, m.start()),
                    client="fetch",
                    method=method_m.group(1) if method_m else "GET",
                    target=m.group(1),
                    snippet=window.splitlines()[0][:120],
                )
            )
        for m in _AXIOS_RE.finditer(text):
            calls.append(
                APICall(
                    file=path,
                    line=line_of(text, m.start()),
                    client="axios",
                    method=m.group(1).upper(),
                    target=m.group(2),
                    snippet=text[m.start():m.start() + 120].splitlines()[0],
                )
            )
        for m in _SUPA_RE.finditer(text):
            tail = m.group(2)
            op = "select"
            for kw in ("insert", "update", "delete", "upsert", "select"):
                if f".{kw}(" in tail:
                    op = kw
                    break
            calls.append(
                APICall(
                    file=path,
                    line=line_of(text, m.start()),
                    client="supabase",
                    method=op.upper(),
                    target=m.group(1),
                    snippet=text[m.start():m.start() + 120].splitlines()[0],
                )
            )
        for m in _RQ_RE.finditer(text):
            window = text[m.start():m.start() + 320]
            key_m = _QUERY_KEY_RE.search(window)
            calls.append(
                APICall(
                    file=path,
                    line=line_of(text, m.start()),
                    client="react-query",
                    method=m.group(1).upper(),
                    target=key_m.group(1).strip() if key_m else "(inline queryFn)",
                    snippet=window.splitlines()[0][:120],
                )
            )
    # de-dupe identical call sites
    seen: set[tuple[str, int, str]] = set()
    unique: list[APICall] = []
    for c in calls:
        key = (c.file, c.line, c.target)
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique
