"""End-to-end pipeline orchestration and artifact writing."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from . import reports
from .align.matrix import build_matrix
from .analyze.discover import discover
from .ingest.codebase import scan_codebase
from .ingest.contracts import parse_contracts
from .ingest.requirements import parse_requirements
from .ingest.rules import parse_rules
from .models import PipelineResult
from .plan.planner import build_plan
from .spec.builder import build_all_specs
from .spec.llm import build_provider
from .utils import write_json, write_text


def run_pipeline(config: dict) -> tuple[PipelineResult, dict]:
    out_dir = Path(config["output_dir"])
    specs_dir = out_dir / "04-specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Ingest -------------------------------------------------------------
    print("[1/6] Ingesting requirements, rules, contracts and codebase…")
    inventory = scan_codebase(config["app_path"])
    requirements = parse_requirements(config["requirements"])
    rules = parse_rules(config["rules"])
    target_entities, target_endpoints = parse_contracts(config["contracts"])

    write_json(out_dir / "01-inventory.json", {
        "inputs": {
            "app_path": config["app_path"],
            "requirements": config["requirements"],
            "rules": config["rules"],
            "contracts": config["contracts"],
        },
        "inventory": inventory.summary(),
        "requirements": requirements,
        "rules": rules,
        "target_entities": target_entities,
        "target_endpoints": target_endpoints,
    })
    write_text(
        out_dir / "01-inventory.md",
        reports.render_inventory(
            inventory.summary(),
            {
                "UI codebase": config["app_path"],
                "Requirements": config["requirements"],
                "Business rules": config["rules"],
                "Target contracts": config["contracts"],
            },
        ),
    )

    # 2. Static discovery ---------------------------------------------------
    print("[2/6] Discovering current UI contracts, mock data and call sites…")
    ui_contracts, mock_datasets, api_calls, components = discover(inventory)
    write_json(out_dir / "02-current-contracts.json", {
        "ui_contracts": ui_contracts,
        "mock_datasets": mock_datasets,
        "api_calls": api_calls,
        "components": components,
    })
    write_text(
        out_dir / "02-current-contracts.md",
        reports.render_current_contracts(ui_contracts, mock_datasets, api_calls, components),
    )

    # 3. Alignment -----------------------------------------------------------
    print("[3/6] Building contract alignment matrix…")
    alignments, unmatched_ui, unmatched_target, findings = build_matrix(
        ui_contracts, mock_datasets, target_entities, rules
    )
    write_json(out_dir / "03-alignment-matrix.json", {
        "alignments": alignments,
        "unmatched_ui_contracts": unmatched_ui,
        "unmatched_target_entities": unmatched_target,
        "findings": findings,
    })
    write_text(
        out_dir / "03-alignment-matrix.md",
        reports.render_alignment(alignments, unmatched_ui, unmatched_target, findings),
    )

    # 4. Specs ---------------------------------------------------------------
    print("[4/6] Writing change specifications…")
    provider = build_provider(config)
    specs = build_all_specs(
        alignments, ui_contracts, mock_datasets, components, target_entities,
        target_endpoints, api_calls, rules, requirements, findings, provider,
    )
    write_json(out_dir / "04-specs" / "specs.json", specs)
    write_text(specs_dir / "index.md", reports.render_spec_index(specs))
    for spec in specs:
        write_text(specs_dir / f"{spec.spec_id}.md", reports.render_spec(spec))

    # 5. Plan ----------------------------------------------------------------
    print("[5/6] Sequencing migration plan…")
    plan = build_plan(
        alignments, specs, components, mock_datasets, target_endpoints, api_calls
    )
    write_json(out_dir / "05-tasks.json", plan)
    write_text(out_dir / "05-migration-plan.md", reports.render_plan(plan, findings, specs))

    # 6. Traceability --------------------------------------------------------
    print("[6/6] Emitting traceability matrix…")
    write_text(
        out_dir / "06-traceability-matrix.md",
        reports.render_traceability(
            rules, requirements, target_entities, specs, plan, findings
        ),
    )

    result = PipelineResult(
        inventory=inventory.summary(),
        ui_contracts=ui_contracts,
        mock_datasets=mock_datasets,
        api_calls=api_calls,
        components=components,
        target_entities=target_entities,
        target_endpoints=target_endpoints,
        alignments=alignments,
        unmatched_ui=unmatched_ui,
        unmatched_target=unmatched_target,
        specs=specs,
        plan=plan,
        requirements=requirements,
        rules=rules,
    )
    write_json(out_dir / "pipeline-result.json", result)

    stats = {
        "ui_contracts": len(ui_contracts),
        "mock_datasets": len(mock_datasets),
        "api_calls": len(api_calls),
        "components": len(components),
        "target_entities": len(target_entities),
        "alignments": len(alignments),
        "findings": dict(Counter(f.severity for f in findings)),
        "specs": len(specs),
        "tasks": len(plan),
        "output_dir": str(out_dir),
    }
    return result, stats
