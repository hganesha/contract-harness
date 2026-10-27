"""Dataclasses shared across pipeline stages.

These models are the single vocabulary of the harness: ingestion produces
them, analysis enriches them, alignment/spec/plan consume them and they are
serialized verbatim to the JSON artifacts under ``outputs/``.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# --------------------------------------------------------------------------- #
# Ingestion models
# --------------------------------------------------------------------------- #
@dataclass
class Requirement:
    id: str
    title: str
    body: str
    acceptance: list[str] = field(default_factory=list)
    source_file: str = ""


@dataclass
class BusinessRule:
    id: str
    title: str
    description: str
    applies_to: list[str] = field(default_factory=list)      # entity names
    requires_fields: list[str] = field(default_factory=list)  # entity.field
    acceptance: list[str] = field(default_factory=list)
    source_file: str = ""


# --------------------------------------------------------------------------- #
# Target contracts (from OpenAPI or the simple JSON contract format)
# --------------------------------------------------------------------------- #
@dataclass
class TargetField:
    name: str
    type: str
    required: bool = False
    enum: list[str] = field(default_factory=list)
    format: str = ""
    ref: str = ""                     # referenced entity name, if any
    is_array: bool = False
    nullable: bool = False
    description: str = ""
    rule_ids: list[str] = field(default_factory=list)


@dataclass
class TargetEntity:
    name: str
    fields: list[TargetField] = field(default_factory=list)
    description: str = ""
    source: str = ""                  # e.g. openapi:/components/schemas/Order


@dataclass
class TargetEndpoint:
    method: str
    path: str
    operation_id: str
    request_entity: str = ""
    response_entity: str = ""
    rule_ids: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Discovered (current) UI contracts
# --------------------------------------------------------------------------- #
@dataclass
class UIField:
    name: str
    type_raw: str
    kind: str                         # primitive | object | array | union | enum | ref | any
    required: bool = True
    enum: list[str] = field(default_factory=list)
    ref: str = ""
    children: list["UIField"] = field(default_factory=list)
    source_file: str = ""
    line: int = 0


@dataclass
class UIContract:
    name: str
    kind: str                         # interface | type | enum | inferred
    fields: list[UIField] = field(default_factory=list)
    enum_values: list[str] = field(default_factory=list)
    source_file: str = ""
    line: int = 0
    inferred: bool = False            # inferred from mock data rather than declared


@dataclass
class MockFieldObservation:
    name: str
    observed_types: list[str] = field(default_factory=list)
    samples: list[str] = field(default_factory=list)
    nullable: bool = False
    present_in: int = 0
    records: int = 0


@dataclass
class MockDataset:
    name: str                          # const/variable name
    entity: str                        # best-guess entity name
    file: str
    annotation: str = ""               # e.g. Order[] if typed
    records: int = 0
    fields: list[MockFieldObservation] = field(default_factory=list)


@dataclass
class APICall:
    file: str
    line: int
    client: str                        # fetch | axios | supabase | react-query | other
    method: str
    target: str                        # url / table / query key
    snippet: str = ""


@dataclass
class ComponentInfo:
    name: str
    file: str
    props: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)        # resolved module paths
    contracts_used: list[str] = field(default_factory=list)
    mock_used: list[str] = field(default_factory=list)
    api_used: list[str] = field(default_factory=list)
    field_accesses: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Alignment
# --------------------------------------------------------------------------- #
@dataclass
class Finding:
    severity: str                      # high | medium | low | info
    code: str                          # machine-readable finding code
    entity: str
    field: str
    message: str
    evidence: list[str] = field(default_factory=list)
    rule_ids: list[str] = field(default_factory=list)


@dataclass
class FieldMapping:
    ui_field: str
    ui_type: str
    target_field: str
    target_type: str
    status: str                        # match | rename | type_mismatch | enum_mismatch | ...
    note: str = ""
    required_in_target: bool = False


@dataclass
class EntityAlignment:
    ui_contract: str
    target_entity: str
    match_confidence: float
    field_mappings: list[FieldMapping] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Specs & plan
# --------------------------------------------------------------------------- #
@dataclass
class ChangeSpec:
    spec_id: str
    title: str
    scope: str                         # entity | component | cross_cutting
    target_entity: str
    current_state: str
    target_state: str
    changes: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    rule_ids: list[str] = field(default_factory=list)
    requirement_ids: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


@dataclass
class PlanTask:
    task_id: str
    phase: str
    title: str
    description: str
    files: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    effort: str = "M"                  # S | M | L
    risk: str = "M"
    acceptance: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)          # rule / requirement / spec ids


@dataclass
class PipelineResult:
    inventory: dict[str, Any]
    ui_contracts: list[UIContract]
    mock_datasets: list[MockDataset]
    api_calls: list[APICall]
    components: list[ComponentInfo]
    target_entities: list[TargetEntity]
    target_endpoints: list[TargetEndpoint]
    alignments: list[EntityAlignment]
    unmatched_ui: list[str]
    unmatched_target: list[str]
    specs: list[ChangeSpec]
    plan: list[PlanTask]
    requirements: list[Requirement]
    rules: list[BusinessRule]


# --------------------------------------------------------------------------- #
# Serialization helpers
# --------------------------------------------------------------------------- #
def to_jsonable(obj: Any) -> Any:
    """Convert dataclasses/Paths into JSON-serializable primitives."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    return obj
