# REPO_OPTIMIZATION_V7

## Goal

Restructure the repository so it is easier for:
- Codex to modify safely
- review agents to reason about boundaries
- CI to enforce invariants
- future agents to reuse the system without tribal knowledge

---

## Recommended layout

Use a **code root + state root** model.

## 1. Code root (tracked source repo)

```text
agent-foundation/
  apps/
    artifact_api/
    thin_kb_api/
    eval_runner/
  packages/
    core/
      schemas/
      services/
      stores/
      workflow/
      events/
    openclaw_adapter/
    shared/
  contracts/
    openapi/
    jsonschema/
  agents/
    AGENT_README.md
    role_contracts/
  docs/
    architecture/
    adr/
    runbooks/
  tests/
    unit/
    integration/
    e2e/
    replay/
    property/
    contracts/
  evals/
    datasets/
    corpora/
    reports/
  fixtures/
    sample_tasks/
    sample_kb/
    sample_docs/
    sample_code/
  scripts/
  ops/
    backup/
    restore/
    health/
  migrations/
  generated/
    openapi/
    schemas/
    reports/
  pyproject.toml
  Makefile
  .env.example
```

## 2. State root (outside source repo or separate data repo)

```text
agent-foundation-state/
  tasks/
    active/
    archived/
  kb/
    canonical/
    candidates/
    deprecated/
  indexes/
    sqlite/
    lancedb/
  ledgers/
    task_events/
    kb_events/
    audits/
  replay/
    captured_runs/
  backups/
```

---

## Why this split is better

### Source repo stays reviewable
- less churn
- cleaner commits
- easier PR review
- easier CI

### State root stays operational
- active tasks can change freely
- indexes can rebuild without touching code repo
- backups and archives become explicit

### AI agents get clearer boundaries
- code changes happen in code root
- runtime mutations happen in state root
- generated artifacts are visibly generated

---

## Directory responsibilities

### `apps/`
Executable service entrypoints only.

### `packages/core/`
Domain logic and schemas.
This should become the single home for workflow, object models, and service logic.

### `contracts/`
Normative API and schema contracts.
Only one source of truth should exist here.
Generated copies should go under `generated/`.

### `agents/`
Agent-facing operating docs and role contracts.

### `evals/`
Everything related to gold sets, replay corpora, rankings, and reports.

### `ops/`
Operational scripts and runbooks only.

### `migrations/`
Schema or canonical object migrations.

---

## Immediate repo refactors

### R1. Replace `libs/` with `packages/core/`
Reason:
- more explicit ownership
- better long-term monorepo ergonomics
- easier future split if needed

### R2. Move ADRs under `docs/adr/`
Reason:
- architecture docs should be discoverable and grouped

### R3. Merge duplicate OpenAPI roots
Use:
- `contracts/openapi/` as source of truth
- `generated/openapi/` for generated/exported artifacts

### R4. Remove duplicate plugin docs
Keep one normative adapter spec, one runbook if needed.

### R5. Add `tests/contracts/`, `tests/replay/`, `tests/property/`
Reason:
- current testing discussion is good, but repo structure should enforce it

### R6. Add `evals/` and `fixtures/`
Reason:
- replay and evaluation must stop being hidden in docs

---

## Suggested package boundaries inside `packages/core/`

```text
packages/core/
  schemas/
    common.py
    artifacts.py
    thin_kb.py
    events.py
  services/
    artifact_service.py
    thin_kb_service.py
    writeback_service.py
    retrieval_service.py
  stores/
    artifact_store.py
    kb_store.py
    manifest_store.py
    ledger_store.py
  workflow/
    state_machine.py
    rules.py
  events/
    task_events.py
    kb_events.py
```

This creates a stronger domain boundary than a generic `storage/` bucket.

---

## Final recommendation

Make repo normalization the first optimization wave.
It will reduce future AI maintenance cost more than any new feature.
