"""Command-line entry point."""
from __future__ import annotations

import argparse
import json

from .config import load_config
from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="contract-harness",
        description=(
            "Align Lovable-generated UI code (dummy data) with real data "
            "contracts and business rules: discover → align → spec → plan."
        ),
    )
    p.add_argument("--config", help="Path to a harness JSON config file.")
    p.add_argument("--app", dest="app_path", help="Path to the Lovable export / UI codebase.")
    p.add_argument("--requirements", help="Requirements Markdown file.")
    p.add_argument("--rules", help="Business rules Markdown or JSON file.")
    p.add_argument("--contracts", help="Target contracts (OpenAPI JSON or simple harness JSON).")
    p.add_argument("--out", dest="output_dir", help="Directory for generated artifacts.")
    p.add_argument("--stats-only", action="store_true", help="Print only the final stats block.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    overrides = {
        "app_path": args.app_path,
        "requirements": args.requirements,
        "rules": args.rules,
        "contracts": args.contracts,
        "output_dir": args.output_dir,
    }
    config = load_config(args.config, overrides)
    _result, stats = run_pipeline(config)

    print("\n=== Harness run complete ===")
    print(json.dumps(stats, indent=2))
    print(f"\nArtifacts written under: {stats['output_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
