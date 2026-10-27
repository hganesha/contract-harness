# Lovable Contract Alignment Harness

An **open, dependency-light harness** that takes the four things a Lovable
project usually ends up with…

1. **Requirements** (markdown, `REQ-###` headings)
2. **Business rules** (markdown, `BR-###` headings — or JSON)
3. **Target data contracts** (OpenAPI 3.x JSON/YAML, or a simple JSON format)
4. **The Lovable-generated UI codebase** — React/TS with dummy/mock data

…and produces everything needed to migrate that UI onto the real contracts:

```
                         ┌──────────────────────────────────────────────┐
 requirements.md   ──▶   │ 1. INGEST     parse docs, schemas, walk code   │
 business-rules.md ──▶   ├──────────────────────────────────────────────┤
 target-contracts  ──▶   │ 2. DISCOVER   TS types, mock shapes, API      │
 lovable-app/      ──▶   │    calls, component → data usage              │
                         ├──────────────────────────────────────────────┤
                         │ 3. ALIGN      entity + field-level diff,      │
                         │    enum/type/nullability checks, rule gaps    │
                         ├──────────────────────────────────────────────┤
                         │ 4. SPEC       per-entity / component / rule / │
                         │    API change specs with acceptance criteria  │
                         ├──────────────────────────────────────────────┤
                         │ 5. PLAN       phased, dependency-ordered      │
                         │    migration tasks + traceability matrix      │
                         └──────────────────────────────────────────────┘
                                            │
                                            ▼
              outputs/  (JSON for tooling + Markdown for humans)
```

The deterministic engine uses **only the Python standard library** — no install
step, no API key required. An optional LLM adapter (any OpenAI-compatible
endpoint, including local Ollama) can enrich narrative sections, and the
harness always falls back to deterministic output if it is unavailable.

## Quickstart

```bash
cd contract-harness
python3 run.py --config harness.config.json        # runs the bundled example
python3 -m unittest discover -s tests -v           # 11 tests, no network
```

Or with explicit flags (no config file needed):

```bash
python3 run.py \
  --app        /path/to/lovable-export \
  --requirements docs/requirements.md \
  --rules      docs/business-rules.md \
  --contracts  openapi/order-service.json \
  --out        outputs
```

## Inputs

| Input | Format | Convention |
| --- | --- | --- |
| Requirements | Markdown | `## REQ-001 — Title`; acceptance as `- [ ]` bullets |
| Business rules | Markdown or JSON | `### BR-001 — Title` with `Applies to:`, `Requires fields:`, `Acceptance:` |
| Target contracts | OpenAPI 3.x (JSON/YAML) or simple JSON | see `examples/target-contracts.openapi.json` and `examples/simple-contracts.example.json` |
| UI codebase | directory | any React/TS export; `node_modules`, `dist`, `.next` etc. are skipped |

The Markdown conventions are intentionally minimal — see
`examples/requirements.md` and `examples/business-rules.md`. Rule-to-field
linkage uses `Entity.field` references (e.g. `Order.amounts`, `Customer.tier`),
and OpenAPI field-level `rule_ids` is supported in the simple JSON format.

## What the discovery engine finds

* **Declared contracts** — `interface`, `type`, and `enum` declarations
  (including nested object shapes, unions, generics, locally-declared
  `*Props`), each with `file:line` evidence.
* **Implicit contracts in dummy data** — `.json` fixtures and TS object-literal
  arrays (`export const mockOrders: Order[] = [...]`). Field types, sample
  values, nullability and presence across records are observed, so optional and
  inconsistent dummy fields surface automatically.
* **Data-access calls** — `fetch`, `axios`, Supabase `.from()`, React Query
  `useQuery/useMutation`, with method and target.
* **Component wiring** — imports, props, referenced contracts, mock datasets,
  API calls, and individual field accesses.

## What alignment detects

| Status | Meaning |
| --- | --- |
| `MATCH` | Same field, compatible type (format constraints noted) |
| `FIELD_RENAME` | Same concept, different name (`id` → `orderId`, `qty` → `quantity`) |
| `TYPE_MISMATCH` | Incompatible types / cardinality, adapter required |
| `ENUM_MISMATCH` | Mock values or UI unions violate the target enum (e.g. dummy `"refunded"`) |
| `ENUM_NOT_ENFORCED` | Target has an enum; UI treats the field as free-text |
| `REQUIRED_MISSING` / `OPTIONAL_MISSING` | Target field absent from the UI contract |
| `UI_ONLY_FIELD` | Dummy-only field with no target counterpart — removal candidate |
| `RULE_FIELD_GAP` | A business rule needs a field the UI cannot currently supply |

Name matching is layered: exact → normalized (`camelCase`/`snake_case`/
kebab/plural) → fuzzy similarity → deterministic fallbacks (alias table,
`id → <entity>Id` convention, suffix containment such as `price → unitPrice`).

## Outputs (`outputs/`)

| Artifact | Purpose |
| --- | --- |
| `01-inventory.{json,md}` | Inputs and codebase inventory |
| `02-current-contracts.{json,md}` | Every discovered contract, mock dataset, call site, component map |
| `03-alignment-matrix.{json,md}` | Entity-by-entity field mapping tables + severity-ranked findings with evidence |
| `04-specs/` | `SPEC-E##` entity, `SPEC-C##` component, `SPEC-R##` rule, `SPEC-X01` API specs, each with acceptance checklists |
| `05-migration-plan.md`, `05-tasks.json` | 7-phase plan: freeze → types/adapters → API client → components → rules → cleanup → verification |
| `06-traceability-matrix.md` | `REQ ↔ BR ↔ contract fields ↔ specs ↔ tasks` |
| `pipeline-result.json` | Full machine-readable result for CI/CD or custom reporters |

The bundled example (`examples/lovable-app`) is a small Lovable-style order
console whose dummy data deliberately exhibits every finding class — use it to
benchmark changes to the engine.

## Running against your own Lovable export

1. Download/zip the Lovable project and unzip it locally (the harness only
   reads files; nothing is uploaded).
2. Export your backend contract as OpenAPI JSON, or write the simple JSON
   contract format.
3. Author requirements/rules using the heading conventions above.
4. Run with `--app /path/to/export` and read `03-alignment-matrix.md` first.

## Optional LLM enrichment

Set `llm.enabled` to `true` in the config and export the API key (default env
var `OPENAI_API_KEY`). Any OpenAI-compatible Chat Completions endpoint works:

```json
"llm": {
  "enabled": true,
  "base_url": "http://localhost:11434/v1",
  "api_key_env": "OPENAI_API_KEY",
  "model": "gpt-4o-mini"
}
```

LLM output is appended to entity specs as explicitly-labeled `(LLM suggestion)`
bullets; all findings, mappings and plan structure remain deterministic, and
failures degrade silently to deterministic mode.

## OpenCode integration (optional)

The harness itself is framework-free Python, but the repo ships an OpenCode
glue layer so the terminal agent ([opencode.ai](https://opencode.ai)) can run
the analysis and execute the resulting plan:

| Path | Role |
| --- | --- |
| `opencode.json` | Project config registering the custom commands |
| `AGENTS.md` | Project rules OpenCode loads every session (commands, artifacts, guardrails) |
| `.opencode/agents/contract-migrator.md` | Subagent that executes specs/tasks in dependency order |
| `.opencode/commands/contract-align.md` | `/contract-align` — runs the harness, summarizes findings (analysis-only) |
| `.opencode/commands/contract-execute.md` | `/contract-execute` — executes the next unblocked task from `05-tasks.json` |

Typical flow inside an OpenCode session at the repo root:

```text
/contract-align --app /path/to/lovable-export --contracts openapi.json ...
# review outputs/03-alignment-matrix.md, then:
/contract-execute T-002
# repeat task by task; progress is tracked in outputs/progress.md
```

Without OpenCode installed, these files are inert Markdown/JSON — the
`python3 run.py` CLI and all artifacts work exactly the same.

## Architecture

```
harness/
├── cli.py / pipeline.py      # entry point + stage orchestration
├── config.py / models.py     # config loading; shared dataclasses
├── utils.py                  # quote/bracket-aware TS scanning helpers
├── ingest/                   # requirements, rules, contracts, codebase walker
├── analyze/                  # ts_types, mock_data, api_calls, components, discover
├── align/                    # matcher (entities), diff (fields), matrix (rules)
├── spec/                     # builder (deterministic specs), llm (optional)
├── plan/                     # phased dependency-ordered planner
└── reports.py                # all Markdown renderers
```

## Heuristics and limitations (be deliberate about these)

* Static analysis is **heuristic**, not a full TypeScript compiler. Extremely
  dynamic code (string-computed property names, Proxy-based access) can evade
  the scanners; every finding carries `file:line` evidence for verification.
* Field matching beyond exact/normalized names uses similarity and conventions;
  review medium-confidence pairs in `03-alignment-matrix.md` before executing.
* Nested target objects (e.g. `amounts.tax`) are represented at the object
  level; rule references use leaf names (`Order.amounts`) for gap analysis.
* The planner sequences work and states dependencies; it does not edit code.
  Generated specs are written so an AI coding agent (or a human) can execute
  them task-by-task.

## Development

```bash
python3 -m unittest discover -s tests -v   # unit + full-pipeline smoke tests
```

The tests run the entire pipeline against the bundled example and assert the
expected renames, enum violations, rule gaps, spec links and plan dependency
integrity — extend them alongside any engine change.

## Roadmap / extension points

* AST-grade parsing via optional tree-sitter dependency
* Generated adapter/test scaffolding (zod schemas, MSW fixtures) from specs
* SARIF/GitHub-Annotations exporter for the findings JSON
* Diff mode: re-run after migration and score remediation progress
