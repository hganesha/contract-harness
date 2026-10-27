"""Small text/parsing utilities used by every stage (stdlib only)."""
from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Optional


# --------------------------------------------------------------------------- #
# IO
# --------------------------------------------------------------------------- #
def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def write_json(path: str | Path, data: Any) -> None:
    from .models import to_jsonable

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(to_jsonable(data), fh, indent=2, ensure_ascii=False)


def write_text(path: str | Path, text: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8")


def line_of(text: str, index: int) -> int:
    """1-based line number for a character index."""
    return text.count("\n", 0, index) + 1


# --------------------------------------------------------------------------- #
# Lightweight TS/TSX scanning
# --------------------------------------------------------------------------- #
def strip_comments(text: str) -> str:
    """Remove // and /* */ comments while preserving strings/templates."""
    out: list[str] = []
    i, n = 0, len(text)
    quote = ""
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if quote:
            out.append(ch)
            if ch == "\\" and quote != "`":
                if i + 1 < n:
                    out.append(nxt)
                    i += 2
                    continue
            elif ch == quote:
                quote = ""
            i += 1
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            out.append(ch)
        elif ch == "/" and nxt == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        elif ch == "/" and nxt == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def match_bracket(text: str, open_idx: int) -> int:
    """Given index of an opening bracket, return index of its match.

    Respects quotes. Works for (), {}, [].
    """
    pairs = {"{": "}", "(": ")", "[": "]"}
    opening = text[open_idx]
    closing = pairs[opening]
    depth = 0
    quote = ""
    i = open_idx
    n = len(text)
    while i < n:
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = ""
        elif ch in ("'", '"', "`"):
            quote = ch
        elif ch == opening:
            depth += 1
        elif ch == closing:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def split_top_level(text: str, separators: str = ";,\n") -> list[str]:
    """Split text on separators at bracket depth 0, respecting quotes."""
    parts: list[str] = []
    depth = 0
    quote = ""
    start = 0
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = ""
            continue
        if ch in ("'", '"', "`"):
            quote = ch
        elif ch in "({[":
            depth += 1
        elif ch in ")}]":
            depth -= 1
        elif depth == 0 and ch in separators:
            parts.append(text[start:i])
            start = i + 1
    tail = text[start:]
    if tail.strip():
        parts.append(tail)
    return [p.strip() for p in parts if p.strip()]


# --------------------------------------------------------------------------- #
# Naming
# --------------------------------------------------------------------------- #
def normalize_name(name: str) -> str:
    """camelCase / PascalCase / snake-case / kebab-case -> normalized token."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    s = re.sub(r"[_\-\s]+", " ", s).lower().strip()
    return s.replace(" ", "")


_SINGULAR_RULES = (
    (re.compile(r"ies$"), "y"),
    (re.compile(r"ses$"), "s"),
    (re.compile(r"ches$"), "ch"),
    (re.compile(r"shes$"), "sh"),
    (re.compile(r"xes$"), "x"),
    (re.compile(r"s$"), ""),
)


def singularize(word: str) -> str:
    for rx, repl in _SINGULAR_RULES:
        if rx.search(word):
            return rx.sub(repl, word)
    return word


def entity_from_filename(path: str | Path) -> str:
    stem = Path(path).stem
    stem = re.sub(r"[._-]?(mock|dummy|fixture|sample|data)s?$", "", stem, flags=re.I)
    token = re.split(r"[._\-]", stem)[-1]
    singular = singularize(token)
    return singular[:1].upper() + singular[1:] if singular else token


def name_similarity(a: str, b: str) -> float:
    na, nb = normalize_name(a), normalize_name(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    # singular/plural equivalence
    if singularize(na) == singularize(nb):
        return 0.95
    return SequenceMatcher(None, na, nb).ratio()


def best_match(name: str, candidates: list[str], cutoff: float = 0.72) -> tuple[Optional[str], float]:
    best, best_score = None, 0.0
    for cand in candidates:
        score = name_similarity(name, cand)
        if score > best_score:
            best, best_score = cand, score
    return (best, best_score) if best_score >= cutoff else (None, best_score)


# --------------------------------------------------------------------------- #
# TS value / literal parsing (good enough for mock data)
# --------------------------------------------------------------------------- #
def parse_ts_value(text: str, idx: int = 0) -> tuple[Any, int]:
    """Parse a TS/JSON-ish literal starting at idx.

    Returns (value, index_after). Unknown identifiers are returned as
    ``"<ident:name>"`` so shape inference still works.
    """
    n = len(text)
    while idx < n and text[idx] in " \t\r\n":
        idx += 1
    if idx >= n:
        return None, idx
    ch = text[idx]
    if ch in "'\"`":
        quote = ch
        end = idx + 1
        buf: list[str] = []
        while end < n:
            c = text[end]
            if c == "\\" and end + 1 < n:
                buf.append(text[end + 1])
                end += 2
                continue
            if c == quote:
                break
            buf.append(c)
            end += 1
        return "".join(buf), end + 1
    if ch in "[{":
        close = match_bracket(text, idx)
        if close == -1:
            return None, n
        inner = text[idx + 1:close]
        if ch == "[":
            items = [parse_ts_value(p, 0)[0] for p in split_top_level(inner, ",\n")]
            return items, close + 1
        obj: dict[str, Any] = {}
        for part in split_top_level(inner, ",\n"):
            m = re.match(r"\s*([A-Za-z_$][\w$]*|'[^']+'|\"[^\"]+\")\s*:\s*", part)
            if not m:
                continue
            key = m.group(1).strip("'\"")
            val, _ = parse_ts_value(part, m.end())
            obj[key] = val
        return obj, close + 1
    m = re.match(r"(?:0x[0-9a-fA-F]+|\d+\.\d+|\d+)", text[idx:])
    if m:
        raw = m.group(0)
        val: Any = float(raw) if "." in raw else int(raw)
        return val, idx + len(raw)
    m = re.match(r"true|false|null|undefined", text[idx:])
    if m:
        raw = m.group(0)
        return True if raw == "true" else False if raw == "false" else None, idx + len(raw)
    m = re.match(r"[A-Za-z_$][\w$.]*", text[idx:])
    if m:
        return f"<ident:{m.group(0)}>", idx + m.end()
    return None, idx + 1


def value_kind(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string" if not value.startswith("<ident:") else "identifier"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


def shorten(value: Any, limit: int = 48) -> str:
    s = json.dumps(value, default=str) if not isinstance(value, str) else value
    s = s.replace("\n", " ")
    return s if len(s) <= limit else s[: limit - 1] + "…"
