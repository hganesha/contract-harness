"""Field-level diffing and type compatibility rules."""
from __future__ import annotations

import re

from ..models import (
    FieldMapping,
    Finding,
    MockFieldObservation,
    TargetField,
    UIField,
)
from ..utils import best_match, name_similarity, normalize_name

_SEVERITY_BY_CODE = {
    "TYPE_MISMATCH": "high",
    "ENUM_MISMATCH": "high",
    "REQUIRED_MISSING": "high",
    "REQUIRED_NOT_ENFORCED": "medium",
    "FIELD_RENAME": "medium",
    "OPTIONAL_MISSING": "medium",
    "UI_ONLY_FIELD": "low",
    "FORMAT_CONSTRAINT": "info",
    "RULE_FIELD_GAP": "high",
    "ENUM_NOT_ENFORCED": "medium",
}


def severity(code: str) -> str:
    return _SEVERITY_BY_CODE.get(code, "medium")


# Common dummy-data shorthand -> real contract field names.
_FIELD_ALIASES = {
    "qty": ["quantity"],
    "price": ["unitPrice"],
    "cost": ["unitPrice"],
}


def fallback_field_match(ui_name: str, target_name: str) -> bool:
    """Second-chance matching when fuzzy similarity is too weak.

    Deterministic and conservative: explicit aliases, the ``id -> <entity>Id``
    convention, and suffix containment (``price`` inside ``unitPrice``).
    """
    if target_name in _FIELD_ALIASES.get(ui_name, []):
        return True
    ui_norm = normalize_name(ui_name)
    t_norm = normalize_name(target_name)
    if ui_norm == "id" and t_norm.endswith("id"):
        return True
    if len(ui_norm) >= 4 and t_norm.endswith(ui_norm):
        return True
    return False


def normalize_ui_type(raw: str) -> tuple[str, bool]:
    t = raw.strip().lower()
    is_array = t.endswith("[]") or "array<" in t or "[]" in t
    if "string" in t:
        base = "string"
    elif "number" in t:
        base = "number"
    elif "boolean" in t:
        base = "boolean"
    elif "date" in t:
        base = "date"
    elif "{" in raw:
        base = "object"
    elif re.search(r"[A-Z]", raw):
        base = "object"  # named reference
    else:
        base = "any"
    return base, is_array


def _type_compatibility(ui_field: UIField, target: TargetField) -> tuple[str, str]:
    """Return (status, note) for a paired UI/target field."""
    ui_base, ui_array = normalize_ui_type(ui_field.type_raw)
    if ui_array != target.is_array:
        return (
            "TYPE_MISMATCH",
            f"cardinality differs: UI {'array' if ui_array else 'single'} vs "
            f"target {'array' if target.is_array else 'single'}",
        )

    if target.enum:
        if ui_field.enum:
            missing = sorted(set(target.enum) - set(ui_field.enum))
            extra = sorted(set(ui_field.enum) - set(target.enum))
            if missing or extra:
                bits = []
                if missing:
                    bits.append(f"UI missing enum values {missing}")
                if extra:
                    bits.append(f"UI has invalid values {extra}")
                return "ENUM_MISMATCH", "; ".join(bits)
            return "MATCH", "enum sets identical"
        return "ENUM_NOT_ENFORCED", f"target restricts to enum {target.enum}; UI has no union type"

    if target.type == "string":
        if ui_base == "string":
            if target.format:
                return "MATCH", f"target format constraint: {target.format} (validate at boundary)"
            return "MATCH", ""
        if ui_base == "date":
            return "TYPE_MISMATCH", "serialization adapter needed: JS Date -> ISO string"
        if ui_base == "any":
            return "MATCH", "UI field is untyped"
        return "TYPE_MISMATCH", f"UI type '{ui_field.type_raw}' vs target string"

    if target.type in ("number", "integer"):
        if ui_base == "number":
            if target.type == "integer":
                return "MATCH", "target requires integer"
            return "MATCH", ""
        if ui_base == "any":
            return "MATCH", "UI field is untyped"
        return "TYPE_MISMATCH", f"UI type '{ui_field.type_raw}' vs target {target.type}"

    if target.type == "boolean":
        if ui_base in ("boolean", "any"):
            return "MATCH", "" if ui_base == "boolean" else "UI field is untyped"
        return "TYPE_MISMATCH", f"UI type '{ui_field.type_raw}' vs target boolean"

    if target.type == "object":
        if ui_base in ("object", "any"):
            note = ""
            if target.ref and ui_field.ref and name_similarity(ui_field.ref, target.ref) < 0.72:
                note = f"nested ref differs: UI {ui_field.ref} vs target {target.ref}"
                return "TYPE_MISMATCH", note
            if target.ref:
                note = f"nested entity: {target.ref}"
            return "MATCH", note
        return "TYPE_MISMATCH", f"UI type '{ui_field.type_raw}' vs target object"

    return "MATCH", "" if ui_base == target.type else f"review ({ui_base} vs {target.type})"


def _finding(code: str, entity: str, field: str, message: str, evidence: list[str],
             rule_ids: list[str] | None = None) -> Finding:
    return Finding(
        severity=severity(code),
        code=code,
        entity=entity,
        field=field,
        message=message,
        evidence=evidence,
        rule_ids=rule_ids or [],
    )


def diff_entity(
    entity_name: str,
    ui_fields: list[UIField],
    target_fields: list[TargetField],
    mock_obs: dict[str, MockFieldObservation],
    rule_ids_by_field: dict[str, list[str]],
) -> tuple[list[FieldMapping], list[Finding]]:
    mappings: list[FieldMapping] = []
    findings: list[Finding] = []
    remaining_ui = list(ui_fields)

    for target in target_fields:
        candidate_names = [f.name for f in remaining_ui]
        match_name, score = best_match(target.name, candidate_names)
        if match_name is None:
            # Deterministic second chance: aliases / id convention / suffix.
            for cand in remaining_ui:
                if fallback_field_match(cand.name, target.name):
                    match_name, score = cand.name, 0.5
                    break
        evidence: list[str] = []
        if match_name is None:
            code = "REQUIRED_MISSING" if target.required else "OPTIONAL_MISSING"
            mappings.append(
                FieldMapping(
                    ui_field="—", ui_type="—", target_field=target.name,
                    target_type=target.type + ("[]" if target.is_array else ""),
                    status=code, required_in_target=target.required,
                    note="not represented anywhere in the UI contract",
                )
            )
            findings.append(
                _finding(
                    code, entity_name, target.name,
                    f"Target field '{target.name}' ({target.type}) is not represented in the UI.",
                    evidence, rule_ids_by_field.get(target.name, []),
                )
            )
            continue

        ui_field = next(f for f in remaining_ui if f.name == match_name)
        remaining_ui.remove(ui_field)
        status, note = _type_compatibility(ui_field, target)

        renamed = normalize_name(ui_field.name) != normalize_name(target.name)
        if status == "MATCH" and renamed:
            status, note = "FIELD_RENAME", f"rename '{ui_field.name}' -> '{target.name}'"
        elif renamed and status != "MATCH":
            note = f"rename '{ui_field.name}' -> '{target.name}'; {note}"

        if target.required and not ui_field.required and status == "MATCH":
            findings.append(
                _finding(
                    "REQUIRED_NOT_ENFORCED", entity_name, target.name,
                    f"'{target.name}' is required by the target contract but optional in the UI.",
                    [f"{ui_field.source_file} (declared optional)"],
                    rule_ids_by_field.get(target.name, []),
                )
            )

        # Mock-data evidence for enums / nullability.
        obs = mock_obs.get(ui_field.name)
        if obs:
            evidence.append(
                f"mock data in {obs.records} records; samples={obs.samples}; "
                f"nullable={obs.nullable}"
            )
            if target.enum and obs.samples:
                bad = [s for s in obs.samples if s not in target.enum and s in obs.samples]
                if bad:
                    findings.append(
                        _finding(
                            "ENUM_MISMATCH", entity_name, target.name,
                            f"Mock values {bad} fall outside target enum {target.enum}.",
                            evidence + [f"observed on field '{ui_field.name}'"],
                            rule_ids_by_field.get(target.name, []),
                        )
                    )
            if target.required and obs.nullable:
                findings.append(
                    _finding(
                        "REQUIRED_NOT_ENFORCED", entity_name, target.name,
                        f"'{target.name}' is required but mock data contains null/missing values.",
                        evidence, rule_ids_by_field.get(target.name, []),
                    )
                )

        if status in ("TYPE_MISMATCH", "ENUM_MISMATCH", "ENUM_NOT_ENFORCED"):
            findings.append(
                _finding(
                    status, entity_name, target.name,
                    f"{ui_field.name} -> {target.name}: {note}",
                    evidence + [f"{ui_field.source_file}:{ui_field.line}"],
                    rule_ids_by_field.get(target.name, []),
                )
            )
        elif status == "FIELD_RENAME":
            findings.append(
                _finding(
                    "FIELD_RENAME", entity_name, target.name, note,
                    [f"{ui_field.source_file}:{ui_field.line}"],
                    rule_ids_by_field.get(target.name, []),
                )
            )
        elif target.format and "format constraint" in note:
            findings.append(
                _finding("FORMAT_CONSTRAINT", entity_name, target.name, note, evidence,
                         rule_ids_by_field.get(target.name, []))
            )

        mappings.append(
            FieldMapping(
                ui_field=ui_field.name,
                ui_type=ui_field.type_raw,
                target_field=target.name,
                target_type=target.type + ("[]" if target.is_array else ""),
                status=status,
                note=note,
                required_in_target=target.required,
            )
        )

    # UI-only leftovers = dummy fields with no target counterpart.
    for ui_field in remaining_ui:
        mappings.append(
            FieldMapping(
                ui_field=ui_field.name, ui_type=ui_field.type_raw,
                target_field="—", target_type="—", status="UI_ONLY_FIELD",
                note="dummy-only field: remove or map explicitly",
            )
        )
        findings.append(
            _finding(
                "UI_ONLY_FIELD", entity_name, ui_field.name,
                f"'{ui_field.name}' exists only in UI dummy data and has no target contract field.",
                [f"{ui_field.source_file}:{ui_field.line}"],
            )
        )
    return mappings, findings
