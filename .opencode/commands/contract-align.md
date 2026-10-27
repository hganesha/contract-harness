---
description: Run the alignment harness against a Lovable app and summarize the gaps
agent: build
---

Run the contract alignment harness and report what it found.

Arguments (optional, quoted as one string):
`$ARGUMENTS` — may contain `--app <dir> --requirements <md> --rules <md> --contracts <json> --out <dir>`

Steps:

1. If arguments were provided, run:
   `python3 run.py $ARGUMENTS`
   otherwise run the bundled example:
   `python3 run.py --config harness.config.json`
2. Confirm the run exits 0 and read the printed stats block.
3. Read `outputs/03-alignment-matrix.md` (or the chosen `--out` directory) and
   summarize, in this order:
   - matched entities and confidence
   - high-severity findings grouped by code (TYPE_MISMATCH, ENUM_MISMATCH,
     REQUIRED_MISSING, RULE_FIELD_GAP, …)
   - renames and dummy-only fields
   - unmatched UI contracts and target entities
4. Read `outputs/06-traceability-matrix.md` and list any business rule with no
   spec/task coverage.
5. State the number of specs and planned tasks, and point at
   `outputs/05-migration-plan.md` as the execution entry point.
6. Do not edit application code in this command — it is analysis-only.
