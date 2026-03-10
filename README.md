# agent-foundation

`agent-foundation` is a minimal agent runtime foundation focused on four things:

- durable task artifacts
- a canonical Thin KB backed by JSON source files
- replayable evaluation and release gates
- runtime hardening for state, indexes, ledgers, and recovery

## What Is In The Repository

- `artifact_api`: file-first task artifact service with validated state transitions
- `thin_kb_api`: canonical Thin KB service backed by JSON plus SQLite FTS/index state
- `packages/core/eval`: frozen corpora, replay, threshold checks, baseline comparison, reporting
- `packages/core/pipeline`: Dagster assets for evaluation and reporting
- `openclaw/plugin_adapter`: TypeScript adapter for tool-facing integration

## Runtime Layout Policy

This repository separates source code from runtime state.

By default, runtime roots live outside the repo using host OS state directories. The runtime policy is implemented in `packages/core/config.py`.

Important consequences:

- do not rely on repo-local `tasks/`, `kb/`, `observability/`, `reports/`, or `shadow_runs/`
- canonical KB JSON lives under `${STATE_ROOT}/kb/canonical/`
- SQLite manifest/index data lives under `${STATE_ROOT}/indexes/sqlite/manifest.sqlite3`
- ledgers, replay artifacts, and backups live under `${STATE_ROOT}/ledgers/`, `${STATE_ROOT}/replay/`, and `${STATE_ROOT}/backups/`

Bootstrap the runtime layout:

```bash
python -m apps.cli.main bootstrap-runtime
```

Inspect or prune legacy repo-local runtime directories:

```bash
python -m apps.cli.main cleanup-runtime
python -m apps.cli.main cleanup-runtime --remove-empty
```

## Quick Start

Python 3.11 is recommended.

```bash
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install '.[dev]'
python -m apps.cli.main bootstrap-runtime
uvicorn apps.artifact_api.main:app --reload --port 8081
uvicorn apps.thin_kb_api.main:app --reload --port 8082
pytest -q
```

For the plugin adapter:

```bash
cd openclaw/plugin_adapter
npm install
npm run check
npm test
```

## Environment

- `AGENT_FOUNDATION_STATE_ROOT`: base runtime state root
- `AGENT_FOUNDATION_WORKSPACE_ROOT`: workspace root for worktrees, sandboxes, and temp agent work
- `AGENT_FOUNDATION_TASKS_ROOT`: task artifact root; defaults to `${STATE_ROOT}/tasks`
- `AGENT_FOUNDATION_KB_ROOT`: KB root; defaults to `${STATE_ROOT}/kb`
- `AGENT_FOUNDATION_KB_DB`: manifest DB path; defaults to `${STATE_ROOT}/indexes/sqlite/manifest.sqlite3`
- `AGENT_FOUNDATION_OBSERVABILITY_ROOT`: observability root; defaults to `${STATE_ROOT}/observability`
- `AGENT_FOUNDATION_EVALS_ROOT`: frozen corpora root; defaults to `./evals`
- `AGENT_FOUNDATION_GENERATED_ROOT`: generated convenience outputs; defaults to `./generated`
- `AGENT_FOUNDATION_REPORTS_ROOT`: report output root; defaults to `${GENERATED_ROOT}/reports`
- `AGENT_FOUNDATION_SHADOW_RUNS_ROOT`: replay workspace root; defaults to `${STATE_ROOT}/replay/captured_runs`
- `ARTIFACT_API_BASE_URL`: plugin base URL for the artifact service; defaults to `http://127.0.0.1:8081`
- `THIN_KB_API_BASE_URL`: plugin base URL for the KB service; defaults to `http://127.0.0.1:8082`
- `REQUEST_TIMEOUT_MS`: plugin HTTP timeout in milliseconds; defaults to `5000`
- `OPENCLAW_RUN_ID`: optional run identifier forwarded by the plugin as `x-run-id`

## Frozen Contracts And Source Of Truth

The public contract freeze is represented by:

- `contracts/openapi/artifact_api.v1.json`
- `contracts/openapi/thin_kb_api.v1.json`
- `contracts/jsonschema/*.json`
- `docs/API_COMPATIBILITY.md`
- `NORMATIVE_FILES.md`

`generated/` is non-normative convenience output and may be regenerated. Contract drift gates compare runtime-generated contracts to frozen snapshots under `contracts/`.

Regenerate and verify contract artifacts:

```bash
make contracts-drift
```

## Evaluation, Replay, And Release Gate

Frozen corpora live under `evals/`.

Run replay only:

```bash
python -m apps.cli.main replay
```

Run full eval:

```bash
python -m apps.cli.main eval
```

Run release gate:

```bash
python -m apps.cli.main release-check --profile smoke
```

Materialize Dagster assets:

```bash
python scripts/materialize_eval_assets.py --run-id nightly-smoke
```

Run local Python validation:

```bash
make validate-local
```

Run plugin validation:

```bash
make plugin-check
```

## Recovery And Backup

Create a backup archive of the configured state root:

```bash
python -m apps.cli.main backup-state --output /tmp/agent-foundation-backup.tar.gz
```

Restore into the configured state root:

```bash
python -m apps.cli.main restore-state --archive /tmp/agent-foundation-backup.tar.gz
```

See `docs/RECOVERY_RUNBOOK.md` for the full recovery procedure.

## Repository Layout

```text
apps/
  artifact_api/
  cli/
  thin_kb_api/
packages/
  core/
    eval/
    events/
    pipeline/
    schemas/
    storage/
contracts/
  openapi/
  jsonschema/
evals/
  corpora/
  datasets/
generated/
openclaw/
  plugin_adapter/
tests/
```

## For Coding Agents

See `AGENTS.md` at the repository root for machine-oriented guidance about normative files, runtime path constraints, required validation commands, storage invariants, and common pitfalls when modifying this repository.
