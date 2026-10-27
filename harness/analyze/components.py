"""Map components/pages to the contracts, mock data and API calls they use."""
from __future__ import annotations

import re
from pathlib import Path

from ..models import APICall, ComponentInfo, MockDataset, UIContract
from ..analyze.ts_types import extract_contracts
from ..utils import read_text, strip_comments

_IMPORT_RE = re.compile(r"import\s+(?:type\s+)?(.+?)\s+from\s+['\"]([^'\"]+)['\"]", re.DOTALL)
_DECL_RE = re.compile(r"(?:export\s+default\s+)?(?:function\s+([A-Z]\w*)|const\s+([A-Z]\w*)\s*=)")
_PROPS_DESTRUCTURE_RE = re.compile(r"(?:function\s+\w+|const\s+\w+\s*=)\s*(?:<[^>]+>)?\(\s*\{([^}]*)\}")
_FIELD_ACCESS_RE = re.compile(r"\.([a-z][A-Za-z0-9_]*)\b")
_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx")


def _resolve(specifier: str, source_file: str, root: str) -> str:
    if not specifier.startswith("."):
        return f"pkg:{specifier}"
    base = (Path(root) / Path(source_file).parent / specifier).resolve()
    candidates = [base]
    candidates += [Path(str(base) + ext) for ext in _EXTENSIONS]
    candidates += [base / f"index{ext}" for ext in _EXTENSIONS]
    for cand in candidates:
        if cand.exists():
            return str(cand.relative_to(Path(root).resolve()))
    return f"unresolved:{specifier}"


def _imported_names(clause: str) -> list[str]:
    names: list[str] = []
    brace = re.search(r"\{(.+)\}", clause, re.DOTALL)
    if brace:
        for part in brace.group(1).split(","):
            part = part.strip().replace("type ", "")
            if not part:
                continue
            names.append(part.split(" as ")[-1].strip())
    else:
        m = re.match(r"\s*([A-Za-z_$][\w$]*)", clause)
        if m:
            names.append(m.group(1))
    return [n for n in names if n]


def analyze_component(
    rel_path: str,
    root: str,
    contracts: list[UIContract],
    datasets: list[MockDataset],
    api_calls: list[APICall],
    known_field_names: set[str],
) -> ComponentInfo:
    text = strip_comments(read_text(Path(root) / rel_path))

    decl = _DECL_RE.search(text)
    name = (decl.group(1) or decl.group(2)) if decl else Path(rel_path).stem

    imports: list[str] = []
    local_imported: list[str] = []
    for m in _IMPORT_RE.finditer(text):
        resolved = _resolve(m.group(2), rel_path, root)
        imports.append(f"{m.group(2)} -> {resolved}")
        local_imported.extend(_imported_names(m.group(1)))

    # props: locally declared *Props contract + signature destructure
    props: list[str] = []
    for contract in extract_contracts(str(Path(root) / rel_path)):
        if contract.name.endswith("Props"):
            props.extend(f.name for f in contract.fields)
    dm = _PROPS_DESTRUCTURE_RE.search(text)
    if dm:
        for part in dm.group(1).split(","):
            p = part.strip().split(":")[0].strip()
            if p and re.match(r"^[A-Za-z_$][\w$]*$", p):
                props.append(p)
    props = sorted(set(props))

    contract_names = {c.name for c in contracts}
    mock_names = {d.name for d in datasets}
    contracts_used = sorted(
        {n for n in contract_names if re.search(rf"\b{re.escape(n)}\b", text)}
    )
    mock_used = sorted(
        {d.name for d in datasets if d.name in mock_names and re.search(rf"\b{re.escape(d.name.split('.')[-1])}\b", text)}
    )
    api_used = sorted(
        {f"{c.client}:{c.method} {c.target}" for c in api_calls if c.file == str(Path(root) / rel_path)}
    )
    field_accesses = sorted(
        {m.group(1) for m in _FIELD_ACCESS_RE.finditer(text) if m.group(1) in known_field_names}
    )

    return ComponentInfo(
        name=name,
        file=str(Path(root) / rel_path),
        props=props,
        imports=imports,
        contracts_used=contracts_used,
        mock_used=mock_used,
        api_used=api_used,
        field_accesses=field_accesses,
    )
