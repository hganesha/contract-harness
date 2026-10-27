"""Entity-level matching between discovered UI contracts and target entities."""
from __future__ import annotations

import re

from ..models import MockDataset, TargetEntity, UIContract, UIField
from ..models import MockFieldObservation
from ..utils import best_match, name_similarity


def dataset_to_contract(ds: MockDataset) -> UIContract:
    """Promote an inferred mock dataset to the shape of a declared contract."""
    fields = [
        UIField(
            name=obs.name,
            type_raw=" | ".join(obs.observed_types) or "any",
            kind="primitive" if len(obs.observed_types) == 1 else "union",
            required=not obs.nullable and obs.present_in == obs.records,
            source_file=ds.file,
        )
        for obs in ds.fields
    ]
    return UIContract(
        name=ds.entity,
        kind="inferred",
        fields=fields,
        source_file=ds.file,
        inferred=True,
    )


def build_ui_side(
    contracts: list[UIContract], datasets: list[MockDataset]
) -> tuple[list[UIContract], dict[str, list[MockDataset]]]:
    """Declared contracts first; mock-only entities become inferred contracts."""
    ui_side = [c for c in contracts if c.fields or c.enum_values]
    declared_entities = {c.name.lower() for c in ui_side}

    by_entity: dict[str, list[MockDataset]] = {}
    for ds in datasets:
        by_entity.setdefault(ds.entity.lower(), []).append(ds)

    for entity_key, group in by_entity.items():
        if entity_key not in declared_entities:
            ui_side.append(dataset_to_contract(group[0]))
    return ui_side, by_entity


def match_entities(
    ui_side: list[UIContract], targets: list[TargetEntity]
) -> list[tuple[UIContract, TargetEntity, float]]:
    target_names = [t.name for t in targets]
    pairs: list[tuple[UIContract, TargetEntity, float]] = []
    used_targets: set[str] = set()

    # Greedy, highest-confidence first.
    scored: list[tuple[float, UIContract, str]] = []
    for contract in ui_side:
        match, score = best_match(contract.name, target_names)
        if match:
            scored.append((score, contract, match))
    for score, contract, match_name in sorted(scored, key=lambda x: -x[0]):
        if match_name in used_targets:
            continue
        target = next(t for t in targets if t.name == match_name)
        pairs.append((contract, target, round(score, 2)))
        used_targets.add(match_name)
    return pairs


def mock_samples_for(
    target_name: str, datasets_by_entity: dict[str, list[MockDataset]]
) -> dict[str, MockFieldObservation]:
    """Field observations from mock data for a target entity (fuzzy entity)."""
    for key, group in datasets_by_entity.items():
        if name_similarity(key, target_name) >= 0.72:
            return {obs.name: obs for ds in group for obs in ds.fields}
    return {}
