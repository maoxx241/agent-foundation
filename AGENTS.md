# AGENTS.md

## Repository purpose

`agent-foundation` is a minimal agent runtime foundation with four main surfaces:

- `artifact_api`: file-first task artifact service with validated state transitions.
- `thin_kb_api`: canonical Thin KB service backed by JSON source files plus a SQLite index.
- `packages/core/eval` and `packages/core/pipeline`: frozen corpus evaluation, replay, reporting, and Dagster orchestration.
- `openclaw/plugin_adapter`: TypeScript adapter for tool-facing integration.

This repository is optimized for runtime hardening, replayability, frozen contracts, and release gating. Do not treat it as a generic playground.

## Source-of-truth rules

### Normative files

Treat these as source of truth unless a more specific ADR or compatibility doc says otherwise:

- `contracts/openapi/*.json`
- `contracts/jsonschema/*.json`
- `docs/API_COMPATIBILITY.md`
- `packages/core/config.py`
- `apps/artifact_api/main.py`
- `apps/thin_kb_api/main.py`
- `packages/core/schemas/`
- `packages/core/storage/`
- `packages/core/eval/`

### Non-normative files

- `generated/**`

`generated/` is disposable output. Do not edit files under `generated/` to change behavior. Regenerate them from code.

## Runtime layout policy

Runtime state must live outside the source repository.

Do not introduce or rely on repo-local runtime directories such as:

- `tasks/`
- `kb/`
- `observability/`
- `reports/`
- `shadow_runs/`

The runtime policy is implemented in `packages/core/config.py`. If you change runtime paths, update:

- `packages/core/config.py`
- `README.md`
- `docs/RECOVERY_RUNBOOK.md`
- any affected tests

## Storage invariants

- Canonical KB JSON under `${KB_ROOT}/canonical/` is the durable source of truth.
- SQLite manifest/index data is derived state, not the source of truth.
- The canonical manifest DB location should be `${STATE_ROOT}/indexes/sqlite/manifest.sqlite3`.
- Backup/restore code may accept older archive layouts for compatibility, but new docs and new code paths should target the canonical location above.

## Contracts and compatibility

When changing request/response models, service routes, or public schemas:

1. update the implementation first;
2. regenerate contract artifacts;
3. confirm frozen contracts under `contracts/` are updated intentionally;
4. run the contract drift check;
5. update compatibility docs if the public surface changed.

Do not hand-edit frozen OpenAPI or JSON schema snapshots unless the change is intentional and verified against the actual app/model construction path.
Contract drift gates compare runtime-generated contracts to frozen snapshots under `contracts/`; `generated/` is not a release gate input.

## Required local commands

For Python changes:

```bash
make validate-local
```

For plugin changes:

```bash
make plugin-check
```

For explicit release gating:

```bash
python -m apps.cli.main release-check --profile smoke
```

For runtime bootstrap:

```bash
python -m apps.cli.main bootstrap-runtime
```

## Release-gate expectations

A change is not ready if it breaks any of the following:

- contract drift checks
- replay / eval thresholds
- baseline comparison policy
- runtime path policy
- plugin type/test checks

When touching evaluation logic, check both metrics and filesystem side effects.

## Evaluation and replay rules

- Frozen corpora live under `evals/`.
- Reports are written under the configured reports root.
- Replay workspaces must not escape the runtime layout policy.
- Do not reintroduce repo-local `shadow_runs` via helper constructors or Dagster entrypoints.

## Change guidance by area

### If you touch runtime paths

Also inspect:

- `packages/core/pipeline/dagster_defs.py`
- `packages/core/eval/runner.py`
- `packages/core/storage/recovery.py`

### If you touch backup/restore

Also inspect:

- manifest DB path assumptions
- archive layout compatibility
- path traversal protections
- runbook examples

### If you touch plugin adapter code

Keep README, CI, and Makefile in sync about the exact commands that must pass.

## Common mistakes to avoid

- Treating `generated/` as normative state.
- Writing runtime state inside the repo.
- Documenting `${KB_ROOT}/manifest.sqlite3` as the canonical manifest DB location if code uses `indexes/sqlite/manifest.sqlite3`.
- Updating README without updating runbooks or tests.
- Changing public contracts without regenerating frozen snapshots.
- Passing `repo_root` to evaluation helpers in ways that recreate repo-local `shadow_runs`.

## Preferred review style

For non-trivial changes, keep patches narrow and internally consistent:

- one PR for runtime/gate semantics
- one PR for CI/doc consistency
- one PR for agent-facing docs

Prefer explicit invariants over convenience shortcuts.
