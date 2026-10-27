---
description: Execute migration tasks from outputs/05-tasks.json in dependency order
agent: contract-migrator
---

Execute the next batch of migration work produced by the harness.

Arguments (optional): `$ARGUMENTS` — a task id (e.g. `T-003`), a phase name
(e.g. `02-types-and-adapters`), or empty for "next unblocked task".

Steps:

1. If `outputs/05-tasks.json` does not exist, stop and ask to run
   `/contract-align` first.
2. Read `outputs/05-tasks.json`, `outputs/progress.md` (create it if missing)
   and the relevant `outputs/04-specs/SPEC-*.md` files.
3. Select the task(s) matching the argument, or the lowest-numbered task whose
   `depends_on` are all marked done. Respect dependency order strictly.
4. Execute the task following the contract-migrator agent protocol; verify each
   finding against its `file:line` evidence before editing.
5. After edits, run any available checks (`python3 -m unittest discover -s tests -v`
   for harness changes; the app's own build/lint for UI changes when present).
6. Record the result in `outputs/progress.md`: task id, status, files changed,
   acceptance items checked, and anything blocked.
7. Stop after the selected task/phase and summarize what changed and what is
   now unblocked. Do not bulk-execute the entire plan in one invocation.
