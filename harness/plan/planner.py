"""Produce a phased, dependency-ordered migration plan from the specs."""
from __future__ import annotations

from ..models import (
    APICall,
    ChangeSpec,
    ComponentInfo,
    EntityAlignment,
    MockDataset,
    PlanTask,
    TargetEndpoint,
)

_CHANGE_STATUSES = {
    "FIELD_RENAME", "TYPE_MISMATCH", "ENUM_MISMATCH", "ENUM_NOT_ENFORCED",
    "REQUIRED_MISSING", "OPTIONAL_MISSING", "UI_ONLY_FIELD",
}


def _effort_from_count(n: int) -> str:
    return "S" if n <= 2 else "M" if n <= 6 else "L"


def _risk_from_findings(alignments: list[EntityAlignment]) -> dict[str, str]:
    risk: dict[str, str] = {}
    for alignment in alignments:
        highs = sum(1 for f in alignment.findings if f.severity == "high")
        risk[alignment.target_entity] = "L" if highs >= 3 else "M" if highs >= 1 else "S"
    return risk


def build_plan(
    alignments: list[EntityAlignment],
    specs: list[ChangeSpec],
    components: list[ComponentInfo],
    datasets: list[MockDataset],
    endpoints: list[TargetEndpoint],
    api_calls: list[APICall],
) -> list[PlanTask]:
    tasks: list[PlanTask] = []
    risk_by_entity = _risk_from_findings(alignments)
    spec_by_id = {s.spec_id: s for s in specs}

    def add(**kwargs) -> PlanTask:
        task = PlanTask(task_id=f"T-{len(tasks) + 1:03d}", **kwargs)
        tasks.append(task)
        return task

    # Phase 0 — freeze -------------------------------------------------------
    freeze = add(
        phase="01-contract-freeze",
        title="Snapshot target contracts and scaffold contract tests",
        description=(
            "Vendor the target schemas (OpenAPI/JSON) into the repo and generate "
            "TypeScript types plus response validators so every later phase has a "
            "single source of truth."
        ),
        files=["src/contracts/ (new)", "tests/contract/ (new)"],
        effort="S",
        risk="S",
        acceptance=[
            "Generated types compile with no errors.",
            "A sample fixture fails validation when intentionally corrupted.",
        ],
        refs=["SPEC-X01"],
    )

    # Phase 1 — entity types + adapters -------------------------------------
    adapter_task: dict[str, str] = {}
    for alignment in alignments:
        entity = alignment.target_entity
        spec = next((s for s in specs if s.scope == "entity" and s.target_entity == entity), None)
        change_count = sum(1 for m in alignment.field_mappings if m.status in _CHANGE_STATUSES)
        if change_count == 0:
            continue
        task = add(
            phase="02-types-and-adapters",
            title=f"Rebuild {entity} types and add a mock→contract adapter",
            description=(
                f"Replace the UI's {alignment.ui_contract} shape with the target "
                f"{entity} contract and centralize field renames, type coercions and "
                "enum mapping in one adapter function so components stay declarative."
            ),
            files=(spec.files if spec else []),
            depends_on=[freeze.task_id],
            effort=_effort_from_count(change_count),
            risk=risk_by_entity.get(entity, "M"),
            acceptance=[
                f"Adapter maps every legacy {alignment.ui_contract} field to {entity} (exhaustive switch).",
                "Adapter unit tests cover nulls, unknown enum values and missing optional fields.",
            ],
            refs=[spec.spec_id] if spec else [],
        )
        adapter_task[entity] = task.task_id

    # Phase 2 — API client ---------------------------------------------------
    api_task: dict[str, str] = {}
    x01 = spec_by_id.get("SPEC-X01")
    for ep in endpoints:
        entity = ep.response_entity or ep.request_entity
        deps = [freeze.task_id]
        if entity in adapter_task:
            deps.append(adapter_task[entity])
        task = add(
            phase="03-api-client",
            title=f"Add typed client for {ep.method} {ep.path}",
            description=(
                "Create one typed client function with runtime response validation; "
                "wire query keys/caching consistent with the existing data layer."
            ),
            files=x01.files if x01 else [],
            depends_on=deps,
            effort="S",
            risk="S",
            acceptance=[
                f"Calling {ep.operation_id} returns a validated {entity or 'response'} type.",
                "Network and validation errors surface through a typed error channel.",
            ],
            refs=["SPEC-X01", *(ep.rule_ids)],
        )
        api_task[ep.path] = task.task_id
    if not endpoints:
        add(
            phase="03-api-client",
            title="Establish the API client layer",
            description="No target endpoints were provided; design the client module around the entity adapters.",
            depends_on=[freeze.task_id],
            effort="M",
            risk="M",
            acceptance=["Client module exists and is consumed by at least one hook."],
            refs=["SPEC-X01"],
        )

    # Phase 3 — component migration ------------------------------------------
    component_task: dict[str, str] = {}
    for spec in specs:
        if spec.scope != "component":
            continue
        comp_name = spec.title.replace("Migrate component ", "").split(" ")[0]
        related_entities = [
            entity for entity, tid in adapter_task.items()
            if any(entity in change for change in spec.changes)
        ]
        deps = [adapter_task[e] for e in related_entities if e in adapter_task]
        deps += list(api_task.values()) if api_task else [freeze.task_id]
        task = add(
            phase="04-component-migration",
            title=f"Migrate {comp_name} to live data and target field names",
            description="; ".join(spec.changes[:3]) + (" …" if len(spec.changes) > 3 else ""),
            files=spec.files,
            depends_on=sorted(set(deps)) or [freeze.task_id],
            effort=_effort_from_count(len(spec.changes)),
            risk="M",
            acceptance=spec.acceptance_criteria,
            refs=[spec.spec_id],
        )
        component_task[comp_name] = task.task_id

    # Phase 4 — business rules -----------------------------------------------
    for spec in specs:
        if spec.scope != "cross_cutting" or not spec.rule_ids:
            continue
        deps = [
            adapter_task[entity]
            for entity in spec.target_entity.split(", ")
            if entity in adapter_task
        ]
        add(
            phase="05-business-rules",
            title=f"Enforce {', '.join(spec.rule_ids)} in the domain layer",
            description=spec.current_state,
            files=[],
            depends_on=deps or [freeze.task_id],
            effort="M",
            risk=risk_by_entity.get(spec.target_entity.split(", ")[0], "M"),
            acceptance=spec.acceptance_criteria,
            refs=[spec.spec_id, *spec.rule_ids],
        )

    # Phase 5 — cleanup dummy data -------------------------------------------
    mock_file_users: dict[str, list[str]] = {ds.file: [] for ds in datasets}
    for comp in components:
        if comp.mock_used:
            for ds in datasets:
                if ds.name in comp.mock_used and ds.file in mock_file_users:
                    mock_file_users[ds.file].append(comp.name)
    for mock_file, users in mock_file_users.items():
        deps = [component_task[u] for u in users if u in component_task]
        add(
            phase="06-cleanup",
            title=f"Delete dummy data module {mock_file}",
            description=(
                "Remove the mock module and any re-exports once every consuming "
                "component reads live data. Search the repo for the const names to "
                "confirm zero references."
            ),
            files=[mock_file],
            depends_on=deps or [freeze.task_id],
            effort="S",
            risk="S",
            acceptance=[f"No import of {mock_file} remains; production build succeeds."],
            refs=[s.spec_id for s in specs if mock_file in s.files],
        )

    # Phase 6 — verification --------------------------------------------------
    add(
        phase="07-verification",
        title="Contract, rule and visual verification",
        description=(
            "Run the full verification sweep: contract tests against recorded "
            "fixtures, business-rule tests with violation cases, and visual QA of "
            "loading/empty/error states on every migrated screen."
        ),
        depends_on=[t.task_id for t in tasks if t.phase.startswith(("04", "05", "06"))],
        effort="M",
        risk="S",
        acceptance=[
            "All contract tests pass against target fixtures.",
            "Every business rule has at least one happy-path and one violation test.",
            "No dummy data references remain in the codebase.",
            "Migrated screens verified for loading, empty and error states.",
        ],
        refs=[s.spec_id for s in specs],
    )
    return tasks
