"""Discover dummy/mock data and infer the *implicit* contracts it carries.

Two sources:

* ``.json`` fixture files (top-level arrays of objects)
* ``.ts``/``.tsx`` const declarations whose initializer is an array of object
  literals (the standard Lovable mock pattern, e.g.
  ``export const mockOrders: Order[] = [ { ... } ]``)

Each record's value types are observed across the whole dataset, so optional
fields and nullable fields surface even when the first record omits them.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from ..models import MockDataset, MockFieldObservation
from ..utils import (
    entity_from_filename,
    parse_ts_value,
    read_text,
    shorten,
    singularize,
    strip_comments,
    value_kind,
)

_CONST_RE = re.compile(r"(?:export\s+)?const\s+([A-Za-z_$][\w$]*)\s*(?::\s*([^=]+?))?\s*=\s*")


def _entity_from_annotation(annotation: str, fallback: str) -> str:
    ann = annotation.strip()
    m = re.search(r"([A-Za-z_$][\w$]*)\s*\[\]", ann)
    if m:
        return m.group(1)
    m = re.search(r"Array<\s*([A-Za-z_$][\w$]*)", ann)
    if m:
        return m.group(1)
    return fallback


def _observe(records: list[dict]) -> list[MockFieldObservation]:
    all_keys: list[str] = []
    for rec in records:
        for k in rec:
            if k not in all_keys:
                all_keys.append(k)
    observations: list[MockFieldObservation] = []
    n = len(records)
    for key in all_keys:
        types: list[str] = []
        samples: list[str] = []
        nullable = False
        present = 0
        for rec in records:
            if key not in rec:
                nullable = True
                continue
            present += 1
            val = rec[key]
            kind = value_kind(val)
            if kind == "null":
                nullable = True
            if kind not in types:
                types.append(kind)
            if len(samples) < 3 and val is not None:
                samples.append(shorten(val))
        observations.append(
            MockFieldObservation(
                name=key,
                observed_types=types,
                samples=samples,
                nullable=nullable,
                present_in=present,
                records=n,
            )
        )
    return observations


def _dataset(name: str, entity: str, file: str, annotation: str, records: list[dict]) -> MockDataset:
    return MockDataset(
        name=name,
        entity=entity,
        file=file,
        annotation=annotation,
        records=len(records),
        fields=_observe(records),
    )


def scan_json_fixture(path: str) -> list[MockDataset]:
    payload = json.loads(read_text(path))
    datasets: list[MockDataset] = []
    if isinstance(payload, list) and payload and all(isinstance(r, dict) for r in payload):
        entity = entity_from_filename(path)
        datasets.append(_dataset(Path(path).stem, entity, path, "", payload))
    elif isinstance(payload, dict):
        for key, val in payload.items():
            if isinstance(val, list) and val and all(isinstance(r, dict) for r in val):
                entity = singularize(key)[:1].upper() + singularize(key)[1:]
                datasets.append(_dataset(key, entity, path, "", val))
    return datasets


def scan_ts_mocks(path: str) -> list[MockDataset]:
    text = strip_comments(read_text(path))
    datasets: list[MockDataset] = []
    fallback_entity = entity_from_filename(path)

    for m in _CONST_RE.finditer(text):
        const_name, annotation = m.group(1), (m.group(2) or "").strip()
        value, _end = parse_ts_value(text, m.end())
        if isinstance(value, list) and value and all(isinstance(r, dict) for r in value):
            entity = _entity_from_annotation(annotation, fallback_entity)
            datasets.append(_dataset(const_name, entity, path, annotation, value))
        elif isinstance(value, dict):
            # const mocks = { orders: [ {...} ] }
            for key, val in value.items():
                if isinstance(val, list) and val and all(isinstance(r, dict) for r in val):
                    entity = singularize(key)[:1].upper() + singularize(key)[1:]
                    datasets.append(
                        _dataset(f"{const_name}.{key}", entity, path, annotation, val)
                    )
    return datasets


def scan_mock_data(json_files: list[str], ts_files: list[str]) -> list[MockDataset]:
    out: list[MockDataset] = []
    for f in json_files:
        try:
            out.extend(scan_json_fixture(f))
        except (json.JSONDecodeError, OSError):
            continue
    for f in ts_files:
        try:
            out.extend(scan_ts_mocks(f))
        except OSError:
            continue
    # de-dupe: same const name + file
    seen: set[tuple[str, str]] = set()
    unique: list[MockDataset] = []
    for ds in out:
        key = (ds.name, ds.file)
        if key not in seen:
            seen.add(key)
            unique.append(ds)
    return unique
