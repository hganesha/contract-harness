"""Walk a Lovable-exported codebase and classify its source files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {
    "node_modules", "dist", "build", ".git", ".next", "coverage",
    ".cache", "out", ".vercel",
}
CODE_EXT = {".ts", ".tsx", ".js", ".jsx", ".json"}


@dataclass
class CodebaseInventory:
    root: str
    code_files: list[str] = field(default_factory=list)
    ts_files: list[str] = field(default_factory=list)
    json_files: list[str] = field(default_factory=list)
    component_files: list[str] = field(default_factory=list)
    page_files: list[str] = field(default_factory=list)
    data_files: list[str] = field(default_factory=list)
    type_files: list[str] = field(default_factory=list)
    lib_files: list[str] = field(default_factory=list)

    def summary(self) -> dict[str, int]:
        return {
            "code_files": len(self.code_files),
            "ts_files": len(self.ts_files),
            "json_files": len(self.json_files),
            "component_files": len(self.component_files),
            "page_files": len(self.page_files),
            "data_files": len(self.data_files),
            "type_files": len(self.type_files),
            "lib_files": len(self.lib_files),
        }


def _rel(root: Path, p: Path) -> str:
    return str(p.relative_to(root))


def scan_codebase(root: str) -> CodebaseInventory:
    root_path = Path(root).resolve()
    if not root_path.exists():
        raise SystemExit(f"UI codebase path does not exist: {root}")
    inv = CodebaseInventory(root=str(root_path))

    for path in sorted(root_path.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file() or path.suffix not in CODE_EXT:
            continue
        rel = _rel(root_path, path)
        inv.code_files.append(rel)
        parts = set(path.parts)
        if path.suffix == ".json":
            inv.json_files.append(rel)
            continue
        inv.ts_files.append(rel)
        if "components" in parts:
            inv.component_files.append(rel)
        elif "pages" in parts or "routes" in parts:
            inv.page_files.append(rel)
        elif "data" in parts or "fixtures" in parts or "mocks" in parts:
            inv.data_files.append(rel)
        elif "types" in parts or path.name in ("types.ts", "models.ts", "schema.ts"):
            inv.type_files.append(rel)
        elif "lib" in parts or "services" in parts or "api" in parts:
            inv.lib_files.append(rel)
    return inv
