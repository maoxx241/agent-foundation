# REPO_SHAPE_V8

## Final target shape

Use a **three-surface layout**:

1. **code root** — versioned source of truth for implementation
2. **state root** — mutable runtime data, indexes, ledgers, archives
3. **workspace root** — optional transient workspaces/worktrees for agents

---

## Code root

```text
agent-foundation/
  apps/
    artifact_api/
    thin_kb_api/
    eval_api/
    openclaw_adapter/
    cli/
  packages/
    core/
      schemas/
      artifacts/
      thin_kb/
      workflow/
      events/
      config/
      auth/
      replay/
      eval/
      observability/
    shared/
  contracts/
    openapi/
    jsonschema/
    events/
  agents/
    AGENT_SYSTEM_README_V2.md
    role_contracts/
    prompts/
  docs/
    architecture/
    adr/
    runbooks/
  tests/
    unit/
    integration/
    contracts/
    replay/
    property/
    recovery/
    security/
    eval/
  evals/
    datasets/
    corpora/
    manifests/
    reports/
  fixtures/
    sample_tasks/
    sample_kb/
    sample_events/
    sample_docs/
    sample_code/
  ops/
    backup/
    restore/
    health/
    migrations/
    maintenance/
  scripts/
  generated/
    openapi/
    jsonschema/
    reports/
  pyproject.toml
  Makefile
  .env.example
```

---

## State root

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
    replay_runs/
    eval_runs/
    releases/
  replay/
    captured_runs/
  backups/
  tmp/
```

---

## Workspace root

```text
agent-foundation-work/
  worktrees/
  sandboxes/
  agent_tmp/
```

---

## Structural rules

### Rule 1 — one normative contract source

Only `contracts/` may contain normative contracts.
Everything under `generated/` is derived.

### Rule 2 — runtime data never lives in the code root

No active tasks, mutable KB state, indexes, or ledgers should be written into the code repo.

### Rule 3 — replay/eval are not hidden under tests only

`tests/` checks correctness.
`evals/` measures system behavior and quality.

### Rule 4 — event ledgers are append-only

Events may be superseded by later events but not rewritten in place.

### Rule 5 — agent prompts/contracts are code-adjacent

Agent operating rules live under `agents/`, not scattered across random docs.

---

## Recommended package ownership

### `packages/core/schemas`
Canonical Pydantic models only.

### `packages/core/artifacts`
Artifact domain logic and file layout helpers.

### `packages/core/thin_kb`
Claim / Procedure / Case / Decision logic.

### `packages/core/workflow`
Task state machine and gate enforcement.

### `packages/core/events`
Event models, append-only writers, readers, projections.

### `packages/core/replay`
Replay manifests, runners, report models.

### `packages/core/eval`
Retrieval and workflow evaluation logic.

### `packages/core/config`
Environment profiles, path policy, startup validation.

### `packages/core/auth`
Service tokens/shared secrets and permission helpers.
