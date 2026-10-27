"""Build the full alignment matrix, including business-rule coverage."""
from __future__ import annotations

from ..models import (
    BusinessRule,
    EntityAlignment,
    Finding,
    MockDataset,
    TargetEntity,
    UIContract,
)
from .diff import diff_entity, severity
from .matcher import build_ui_side, match_entities, mock_samples_for

_GAP_STATUSES = {
    "REQUIRED_MISSING", "OPTIONAL_MISSING", "TYPE_MISMATCH",
    "ENUM_MISMATCH", "ENUM_NOT_ENFORCED",
}


def _rule_index_by_entity(
    targets: list[TargetEntity], rules: list[BusinessRule]
) -> dict[str, dict[str, list[str]]]:
    index: dict[str, dict[str, list[str]]] = {t.name: {} for t in targets}
    for target in targets:
        for fld in target.fields:
            index[target.name][fld.name] = list(fld.rule_ids)
    for rule in rules:
        for ref in rule.requires_fields:
            parts = ref.split(".")
            entity, leaf = parts[0], parts[-1]
            for target in targets:
                if target.name.lower() != entity.lower():
                    continue
                if any(f.name == leaf for f in target.fields):
                    index[target.name].setdefault(leaf, [])
                    if rule.id not in index[target.name][leaf]:
                        index[target.name][leaf].append(rule.id)
    return index


def build_matrix(
    contracts: list[UIContract],
    datasets: list[MockDataset],
    targets: list[TargetEntity],
    rules: list[BusinessRule],
) -> tuple[list[EntityAlignment], list[str], list[str], list[Finding]]:
    ui_side, datasets_by_entity = build_ui_side(contracts, datasets)
    pairs = match_entities(ui_side, targets)

    matched_ui = {c.name for c, _t, _s in pairs}
    matched_target = {t.name for _c, t, _s in pairs}
    unmatched_ui = [c.name for c in ui_side if c.name not in matched_ui]
    unmatched_target = [t.name for t in targets if t.name not in matched_target]

    rule_index = _rule_index_by_entity(targets, rules)
    alignments: list[EntityAlignment] = []
    global_findings: list[Finding] = []

    for ui_contract, target, score in pairs:
        mock_obs = mock_samples_for(target.name, datasets_by_entity)
        mappings, findings = diff_entity(
            target.name,
            ui_contract.fields,
            target.fields,
            mock_obs,
            rule_index.get(target.name, {}),
        )

        # Rule coverage: any rule-required field that is a gap becomes a
        # high-severity, rule-linked finding.
        mapping_by_target = {m.target_field: m for m in mappings if m.target_field != "—"}
        for rule in rules:
            if target.name not in rule.applies_to and rule.applies_to:
                continue
            for ref in rule.requires_fields:
                leaf = ref.split(".")[-1]
                mapping = mapping_by_target.get(leaf)
                if mapping and mapping.status in _GAP_STATUSES:
                    findings.append(
                        Finding(
                            severity=severity("RULE_FIELD_GAP"),
                            code="RULE_FIELD_GAP",
                            entity=target.name,
                            field=leaf,
                            message=(
                                f"{rule.id} requires '{leaf}' but the UI currently has "
                                f"{mapping.status.lower()} ({mapping.ui_field})."
                            ),
                            evidence=[f"rule: {rule.title}"],
                            rule_ids=[rule.id],
                        )
                    )

        alignments.append(
            EntityAlignment(
                ui_contract=ui_contract.name,
                target_entity=target.name,
                match_confidence=score,
                field_mappings=mappings,
                findings=findings,
            )
        )
        global_findings.extend(findings)

    # Rules targeting entities with no UI representation at all.
    for rule in rules:
        for entity in rule.applies_to:
            if entity in unmatched_target:
                global_findings.append(
                    Finding(
                        severity="high",
                        code="RULE_FIELD_GAP",
                        entity=entity,
                        field="*",
                        message=(
                            f"{rule.id} applies to '{entity}', which has no matching UI "
                            "contract or mock data yet."
                        ),
                        evidence=[f"rule: {rule.title}"],
                        rule_ids=[rule.id],
                    )
                )

    # De-duplicate (rule-gap findings are embedded per alignment AND global).
    seen: set[tuple] = set()
    unique: list[Finding] = []
    for finding in global_findings:
        key = (finding.code, finding.entity, finding.field, finding.message,
               tuple(finding.rule_ids))
        if key not in seen:
            seen.add(key)
            unique.append(finding)
    return alignments, unmatched_ui, unmatched_target, unique
