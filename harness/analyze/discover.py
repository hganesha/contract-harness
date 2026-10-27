"""Orchestrate static discovery over the whole codebase."""
from __future__ import annotations

from pathlib import Path

from ..ingest.codebase import CodebaseInventory
from ..models import APICall, ComponentInfo, MockDataset, UIContract
from .api_calls import scan_api_calls
from .components import analyze_component
from .mock_data import scan_mock_data
from .ts_types import extract_all_contracts


def discover(
    inventory: CodebaseInventory,
) -> tuple[list[UIContract], list[MockDataset], list[APICall], list[ComponentInfo]]:
    root = inventory.root
    abs_paths = lambda rels: [str(Path(root) / r) for r in rels]  # noqa: E731

    # 1. Declared contracts — type files first, then every TS file (components
    #    often declare *Props locally).
    type_files = abs_paths(inventory.type_files or inventory.ts_files)
    contracts = extract_all_contracts(type_files)
    declared_names = {(c.name, c.source_file) for c in contracts}
    for f in abs_paths(inventory.ts_files):
        for c in extract_all_contracts([f]):
            if (c.name, c.source_file) not in declared_names:
                contracts.append(c)
                declared_names.add((c.name, c.source_file))

    # 2. Mock / dummy data.
    datasets = scan_mock_data(
        json_files=abs_paths(inventory.json_files),
        ts_files=abs_paths(inventory.data_files or inventory.ts_files),
    )

    # 3. Network/data-access calls.
    api_calls = scan_api_calls(abs_paths(inventory.ts_files))

    # 4. Components and pages.
    known_field_names: set[str] = set()
    for c in contracts:
        known_field_names.update(f.name for f in c.fields)
    for d in datasets:
        known_field_names.update(f.name for f in d.fields)

    components = [
        analyze_component(rel, root, contracts, datasets, api_calls, known_field_names)
        for rel in inventory.component_files + inventory.page_files
    ]
    return contracts, datasets, api_calls, components
