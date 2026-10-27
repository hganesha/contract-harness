"""Parse target contracts.

Two accepted formats:

1. OpenAPI 3.x (JSON). Entities come from ``components.schemas``; endpoints
   from ``paths`` with request/response ``$ref`` resolution.
2. Simple harness JSON::

       {
         "entities": [
           {"name": "Order", "description": "...",
            "fields": [{"name": "orderId", "type": "string", "required": true,
                        "rule_ids": ["BR-001"]}]}
         ],
         "endpoints": [{"method": "GET", "path": "/orders",
                        "response_entity": "Order"}]
       }

YAML OpenAPI documents are supported when PyYAML is installed; otherwise JSON
is required (keeps the base harness dependency-free).
"""
from __future__ import annotations

import json
import re
from typing import Any

from ..models import TargetEndpoint, TargetEntity, TargetField
from ..utils import read_text

_PRIMITIVES = {"string", "number", "integer", "boolean", "null"}


def _load_doc(path: str) -> dict[str, Any]:
    text = read_text(path)
    if path.endswith((".yaml", ".yml")):
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise SystemExit(
                "PyYAML is required for YAML contracts: pip install pyyaml "
                "(or convert the contract to JSON)."
            ) from exc
        return yaml.safe_load(text)
    return json.loads(text)


def _ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def _schema_to_field(name: str, schema: dict[str, Any], required: bool) -> TargetField:
    f = TargetField(name=name, type="object", required=required)
    schema = schema or {}
    f.description = schema.get("description", "")
    f.enum = [str(v) for v in schema.get("enum", [])]
    f.format = schema.get("format", "")
    f.nullable = schema.get("nullable", False) or "null" in (
        schema.get("type") if isinstance(schema.get("type"), list) else []
    )

    if "$ref" in schema:
        f.ref = _ref_name(schema["$ref"])
        f.type = "object"
        return f

    is_array = schema.get("type") == "array" or "items" in schema
    if is_array:
        f.is_array = True
        items = schema.get("items", {})
        if "$ref" in items:
            f.ref = _ref_name(items["$ref"])
            f.type = "object"
        else:
            f.type = items.get("type", "any")
            f.format = items.get("format", f.format)
            f.enum = [str(v) for v in items.get("enum", [])]
        return f

    f.type = schema.get("type", "any")
    if isinstance(f.type, list):  # type: ['string', 'null']
        f.type = next((t for t in f.type if t != "null"), "any")
    if "allOf" in schema:
        for sub in schema["allOf"]:
            if "$ref" in sub:
                f.ref = _ref_name(sub["$ref"])
                f.type = "object"
    return f


def _parse_openapi(doc: dict[str, Any]) -> tuple[list[TargetEntity], list[TargetEndpoint]]:
    entities: list[TargetEntity] = []
    schemas = doc.get("components", {}).get("schemas", {})
    for entity_name, schema in schemas.items():
        required = set(schema.get("required", []))
        props = schema.get("properties", {})
        fields = [
            _schema_to_field(prop_name, prop_schema, prop_name in required)
            for prop_name, prop_schema in props.items()
        ]
        entities.append(
            TargetEntity(
                name=entity_name,
                fields=fields,
                description=schema.get("description", ""),
                source=f"openapi:/components/schemas/{entity_name}",
            )
        )

    endpoints: list[TargetEndpoint] = []
    for path, ops in doc.get("paths", {}).items():
        if not isinstance(ops, dict):
            continue
        for method, op in ops.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            ep = TargetEndpoint(
                method=method.upper(),
                path=path,
                operation_id=op.get("operationId", f"{method.upper()} {path}"),
            )
            content = (op.get("requestBody", {}).get("content", {}) or {})
            json_body = content.get("application/json", {})
            ref = (json_body.get("schema", {}) or {}).get("$ref")
            if ref:
                ep.request_entity = _ref_name(ref)
            for code, resp in (op.get("responses", {}) or {}).items():
                if not str(code).startswith("2"):
                    continue
                schema = (
                    (resp.get("content", {}) or {})
                    .get("application/json", {})
                    .get("schema", {})
                    or {}
                )
                if "$ref" in schema:
                    ep.response_entity = _ref_name(schema["$ref"])
                elif schema.get("type") == "array" and "$ref" in schema.get("items", {}):
                    ep.response_entity = _ref_name(schema["items"]["$ref"])
                elif "allOf" in schema:
                    for sub in schema["allOf"]:
                        if "$ref" in sub:
                            ep.response_entity = _ref_name(sub["$ref"])
                break
            endpoints.append(ep)
    return entities, endpoints


def _parse_simple(doc: dict[str, Any]) -> tuple[list[TargetEntity], list[TargetEndpoint]]:
    entities = [
        TargetEntity(
            name=e["name"],
            description=e.get("description", ""),
            source=e.get("source", "simple-json"),
            fields=[
                TargetField(
                    name=fld["name"],
                    type=fld.get("type", "any"),
                    required=fld.get("required", False),
                    enum=[str(v) for v in fld.get("enum", [])],
                    format=fld.get("format", ""),
                    ref=fld.get("ref", ""),
                    is_array=fld.get("is_array", False),
                    nullable=fld.get("nullable", False),
                    description=fld.get("description", ""),
                    rule_ids=fld.get("rule_ids", []),
                )
                for fld in e.get("fields", [])
            ],
        )
        for e in doc.get("entities", [])
    ]
    endpoints = [
        TargetEndpoint(
            method=ep.get("method", "GET"),
            path=ep["path"],
            operation_id=ep.get("operation_id", f"{ep.get('method', 'GET')} {ep['path']}"),
            request_entity=ep.get("request_entity", ""),
            response_entity=ep.get("response_entity", ""),
            rule_ids=ep.get("rule_ids", []),
        )
        for ep in doc.get("endpoints", [])
    ]
    return entities, endpoints


def parse_contracts(path: str) -> tuple[list[TargetEntity], list[TargetEndpoint]]:
    doc = _load_doc(path)
    if "openapi" in doc or "swagger" in doc:
        return _parse_openapi(doc)
    return _parse_simple(doc)
