"""Render pipeline artifacts as human-readable Markdown."""
from __future__ import annotations

from collections import Counter

from .models import (
    APICall,
    BusinessRule,
    ChangeSpec,
    ComponentInfo,
    EntityAlignment,
    Finding,
    MockDataset,
    PlanTask,
    Requirement,
    TargetEntity,
    UIContract,
)

_BADGE = {"high": "🔴 high", "medium": "🟠 medium", "low": "🟡 low", "info": "🔵 info"}


def _table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(c).replace("\n", " ") for c in row) + " |")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
def render_inventory(inv_summary: dict, inputs: dict) -> str:
    lines = ["# 01 — Input inventory", ""]
    lines.append("## Inputs")
    lines.append(_table(["Input", "Path"], [[k, v] for k, v in inputs.items()]))
    lines.append("")
    lines.append("## Codebase inventory")
    lines.append(_table(["Metric", "Count"], [[k, v] for k, v in inv_summary.items()]))
    return "\n".join(lines) + "\n"


def render_current_contracts(
    contracts: list[UIContract],
    datasets: list[MockDataset],
    api_calls: list[APICall],
    components: list[ComponentInfo],
) -> str:
    lines = ["# 02 — Current contracts discovered in the UI", ""]

    lines.append(f"## Declared TypeScript contracts ({len(contracts)})")
    for c in contracts:
        tag = " (enum)" if c.kind == "enum" else ""
        lines.append(f"### `{c.name}`{tag} — {c.source_file}:{c.line}")
        if c.enum_values:
            lines.append("Values: `" + "`, `".join(c.enum_values) + "`")
        if c.fields:
            rows = [
                [f.name, "optional" if not f.required else "required", f.type_raw, f.kind]
                for f in c.fields
            ]
            lines.append(_table(["Field", "Cardinality", "TS type", "Kind"], rows))
        lines.append("")

    lines.append(f"## Mock / dummy datasets ({len(datasets)})")
    for ds in datasets:
        lines.append(f"### `{ds.name}` → inferred entity **{ds.entity}** — {ds.file}")
        lines.append(f"Records: {ds.records}; annotation: `{ds.annotation or 'none'}`")
        rows = [
            [o.name, ", ".join(o.observed_types), "yes" if o.nullable else "no",
             f"{o.present_in}/{o.records}", ", ".join(o.samples)]
            for o in ds.fields
        ]
        lines.append(_table(
            ["Field", "Observed types", "Nullable", "Present", "Samples"], rows
        ))
        lines.append("")

    lines.append(f"## Data-access call sites ({len(api_calls)})")
    if api_calls:
        lines.append(_table(
            ["Client", "Method", "Target", "Location"],
            [[c.client, c.method, c.target, f"{c.file}:{c.line}"] for c in api_calls],
        ))
    else:
        lines.append("_No fetch/axios/Supabase/React Query calls detected — the UI is fully mock-driven._")
    lines.append("")

    lines.append(f"## Components & pages ({len(components)})")
    rows = []
    for comp in components:
        rows.append([
            comp.name,
            ", ".join(comp.contracts_used) or "—",
            ", ".join(comp.mock_used) or "—",
            ", ".join(comp.api_used) or "—",
            str(len(comp.field_accesses)),
        ])
    lines.append(_table(
        ["Component", "Contracts", "Mock data", "API calls", "Data fields touched"], rows
    ))
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
def render_alignment(
    alignments: list[EntityAlignment],
    unmatched_ui: list[str],
    unmatched_target: list[str],
    findings: list[Finding],
) -> str:
    counts = Counter(f.severity for f in findings)
    lines = [
        "# 03 — Contract alignment matrix",
        "",
        "Finding counts: " + ", ".join(
            f"{_BADGE.get(s, s)} **{n}**" for s, n in sorted(counts.items())
        ) or "No findings.",
        "",
    ]
    for alignment in alignments:
        lines.append(
            f"## `{alignment.ui_contract}` → **{alignment.target_entity}** "
            f"(confidence {alignment.match_confidence})"
        )
        rows = [
            [m.ui_field, m.ui_type, m.target_field, m.target_type,
             "required" if m.required_in_target else "optional", m.status, m.note]
            for m in alignment.field_mappings
        ]
        lines.append(_table(
            ["UI field", "UI type", "Target field", "Target type", "Target req.", "Status", "Note"],
            rows,
        ))
        if alignment.findings:
            lines.append("")
            lines.append("**Findings**")
            for f in alignment.findings:
                lines.append(
                    f"- {_BADGE.get(f.severity, f.severity)} `{f.code}` — **{f.field}**: {f.message}"
                )
                for ev in f.evidence:
                    lines.append(f"  - evidence: `{ev}`")
        lines.append("")

    lines.append("## Unmatched")
    lines.append("- UI contracts without a target: " + (", ".join(unmatched_ui) or "none"))
    lines.append("- Target entities without UI representation: " + (", ".join(unmatched_target) or "none"))
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
def render_spec_index(specs: list[ChangeSpec]) -> str:
    lines = ["# 04 — Change specifications", ""]
    lines.append(_table(
        ["Spec", "Scope", "Title", "Rules", "Requirements"],
        [
            [s.spec_id, s.scope, s.title, ", ".join(s.rule_ids) or "—",
             ", ".join(s.requirement_ids) or "—"]
            for s in specs
        ],
    ))
    return "\n".join(lines) + "\n"


def render_spec(spec: ChangeSpec) -> str:
    lines = [f"# {spec.spec_id} — {spec.title}", ""]
    lines.append(f"- **Scope:** {spec.scope}")
    if spec.target_entity:
        lines.append(f"- **Target entity:** {spec.target_entity}")
    if spec.rule_ids:
        lines.append(f"- **Business rules:** {', '.join(spec.rule_ids)}")
    if spec.requirement_ids:
        lines.append(f"- **Requirements:** {', '.join(spec.requirement_ids)}")
    lines.append("")
    lines.append("## Current state")
    lines.append(spec.current_state)
    lines.append("")
    lines.append("## Target state")
    lines.append(spec.target_state)
    lines.append("")
    lines.append("## Required changes")
    lines.extend(f"- {c}" for c in spec.changes)
    lines.append("")
    if spec.files:
        lines.append("## Files in scope")
        lines.extend(f"- `{f}`" for f in spec.files)
        lines.append("")
    lines.append("## Acceptance criteria")
    lines.extend(f"- [ ] {a}" for a in spec.acceptance_criteria)
    if spec.evidence:
        lines.append("")
        lines.append("## Evidence")
        lines.extend(f"- {e}" for e in spec.evidence)
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
def render_plan(tasks: list[PlanTask], findings: list[Finding], specs: list[ChangeSpec]) -> str:
    counts = Counter(f.severity for f in findings)
    lines = [
        "# 05 — Migration plan",
        "",
        "## Executive summary",
        "",
        f"- {len(tasks)} tasks across {len({t.phase for t in tasks})} phases",
        f"- {len(specs)} change specs; findings: "
        + ", ".join(f"{s}={n}" for s, n in sorted(counts.items())),
        f"- Effort: S={sum(t.effort == 'S' for t in tasks)}, "
        f"M={sum(t.effort == 'M' for t in tasks)}, L={sum(t.effort == 'L' for t in tasks)}",
        "",
    ]
    current_phase = ""
    for task in tasks:
        if task.phase != current_phase:
            current_phase = task.phase
            lines.append(f"## Phase {current_phase}")
            lines.append("")
        lines.append(f"### {task.task_id} — {task.title}  `effort:{task.effort}` `risk:{task.risk}`")
        lines.append(task.description)
        if task.depends_on:
            lines.append(f"- **Depends on:** {', '.join(task.depends_on)}")
        if task.files:
            lines.append(f"- **Files:** {', '.join(f'`{f}`' for f in task.files)}")
        if task.refs:
            lines.append(f"- **Refs:** {', '.join(task.refs)}")
        lines.append("- **Acceptance:**")
        lines.extend(f"  - [ ] {a}" for a in task.acceptance)
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
def render_traceability(
    rules: list[BusinessRule],
    requirements: list[Requirement],
    targets: list[TargetEntity],
    specs: list[ChangeSpec],
    tasks: list[PlanTask],
    findings: list[Finding],
) -> str:
    lines = ["# 06 — Traceability matrix", "", "## Business rules → contracts → specs → tasks", ""]
    rows = []
    for rule in rules:
        linked_specs = [s.spec_id for s in specs if rule.id in s.rule_ids]
        linked_tasks = [t.task_id for t in tasks if rule.id in t.refs]
        gap = [f for f in findings if f.rule_ids and f.rule_ids[0] == rule.id]
        rows.append([
            rule.id,
            rule.title,
            ", ".join(rule.applies_to) or "—",
            ", ".join(rule.requires_fields) or "—",
            f"{len(gap)} finding(s)",
            ", ".join(linked_specs) or "—",
            ", ".join(linked_tasks) or "—",
        ])
    lines.append(_table(
        ["Rule", "Title", "Entities", "Required fields", "Gap analysis", "Specs", "Tasks"], rows
    ))
    lines.append("")
    lines.append("## Requirements → affected entities → specs")
    rows = []
    for req in requirements:
        entities = [
            t.name for t in targets
            if t.name.lower() in (req.title + " " + req.body).lower()
        ]
        linked = [s.spec_id for s in specs if req.id in s.requirement_ids]
        rows.append([req.id, req.title, ", ".join(entities) or "—", ", ".join(sorted(set(linked))) or "—"])
    lines.append(_table(["Requirement", "Title", "Entities", "Specs"], rows))
    return "\n".join(lines) + "\n"
