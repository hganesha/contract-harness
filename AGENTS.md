# Project rules — Lovable Contract Alignment Harness

## What this repository is

A standalone Python harness (standard library only, no pip install) that aligns
a Lovable-generated React/TS app (dummy data) with real data contracts and
business rules. Pipeline: ingest → discover → align → spec → plan.

## Commands

```bash
# Full pipeline against the bundled example
python3 run.py --config harness.config.json

# Against a real Lovable export
python3 run.py --app <app-dir> --requirements <req.md> \
  --rules <rules.md> --contracts <openapi.json> --out outputs

# Tests (unit + end-to-end smoke, no network)
python3 -m unittest discover -s tests -v
```

## Artifacts (generated — never hand-edit; regenerate with the harness)

- `outputs/02-current-contracts.md` — discovered TS contracts, mock datasets, call sites
- `outputs/03-alignment-matrix.md` — field-level mapping + severity-ranked findings
- `outputs/04-specs/SPEC-*.md` — entity (E), component (C), rule (R), API (X) specs
- `outputs/05-tasks.json` / `05-migration-plan.md` — phased, dependency-ordered tasks
- `outputs/06-traceability-matrix.md` — REQ ↔ BR ↔ contract ↔ spec ↔ task links

## Rules for any agent editing the Lovable app or the harness

1. The harness is deterministic and heuristic. Before acting on a finding,
   verify it against the cited `file:line` evidence.
2. Execute migration work in plan order (T-001 → …); respect `depends_on` in
   `05-tasks.json`. Never start phase N+1 while phase N tasks are open.
3. Field renames and type coercions belong in a central adapter module, not
   inline in presentational components.
4. Business rules live in the domain/adapter layer with tests (happy path +
   at least one violation case per BR).
5. Do not delete a mock module until `outputs/05-migration-plan.md` cleanup
   phase confirms zero references (grep the const names repo-wide).
6. After any engine change under `harness/`, run the full test suite — it
   asserts the expected renames, enum violations, rule gaps and plan integrity.
7. Keep the harness dependency-free (stdlib only). Optional LLM features go
   behind `harness/spec/llm.py` and must degrade to deterministic output.
