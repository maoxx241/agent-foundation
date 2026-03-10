# agent-foundation

Phase 1 plus the minimal runnable Phase 2 enrichment described in the earlier design packs, now
normalized toward the `design-pack-v7` structure-first plan.

It provides:

- `artifact_api`: file-first task artifact service with validated state transitions
- `thin_kb_api`: canonical Thin KB service backed by JSON files and SQLite FTS5
- `thin_kb_api` Phase 2 enrichment: document/code ingestion, hybrid retrieval, writeback refinement
- `packages/core/eval` + `packages/core/pipeline`: frozen corpora runner, report generation, and Dagster asset orchestration
- `openclaw/plugin_adapter`: thin TypeScript adapter for OpenClaw tools
- `tests`: unit and end-to-end coverage for the happy path and blocked transition path

## Layout

```text
apps/
  artifact_api/
  thin_kb_api/
packages/
  core/
    schemas/
    storage/
    eval/
    pipeline/
contracts/
  openapi/
evals/
  datasets/
  corpora/
generated/
  reports/
openclaw/
  plugin_adapter/
tests/
```

## Local Run

Python 3.11 recommended:

```bash
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install '.[dev]'
uvicorn apps.artifact_api.main:app --reload --port 8081
uvicorn apps.thin_kb_api.main:app --reload --port 8082
pytest
```

Node 22+ for the plugin:

```bash
cd openclaw/plugin_adapter
npm install
npm run check
npm test
```

## Environment

- `AGENT_FOUNDATION_STATE_ROOT`: base runtime root. Defaults outside the source repo using the host OS state directory.
- `AGENT_FOUNDATION_TASKS_ROOT`: overrides the task artifact root. Defaults to `${STATE_ROOT}/tasks`.
- `AGENT_FOUNDATION_KB_ROOT`: overrides the KB root. Defaults to `${STATE_ROOT}/kb`.
- `AGENT_FOUNDATION_KB_DB`: overrides the KB SQLite manifest path. Defaults to `${KB_ROOT}/manifest.sqlite3`.
- `ARTIFACT_API_BASE_URL`: default base URL used by the plugin. Defaults to `http://127.0.0.1:8081`.
- `THIN_KB_API_BASE_URL`: default base URL used by the plugin. Defaults to `http://127.0.0.1:8082`.
- `REQUEST_TIMEOUT_MS`: plugin HTTP timeout in milliseconds. Defaults to `5000`.
- `AGENT_FOUNDATION_OBSERVABILITY_ROOT`: root for JSONL events and metrics. Defaults to `${STATE_ROOT}/observability`.
- `AGENT_FOUNDATION_EVALS_ROOT`: overrides the frozen corpora root. Defaults to `./evals`.
- `AGENT_FOUNDATION_REPORTS_ROOT`: overrides generated reports. Defaults to `./generated/reports`.
- `OPENCLAW_RUN_ID`: optional run identifier forwarded by the plugin as `x-run-id`.

See [`docs/MIGRATION_V7_REPO.md`](./docs/MIGRATION_V7_REPO.md) for the full path migration table.

## Contract Freeze

- Public API compatibility policy: [`docs/API_COMPATIBILITY.md`](./docs/API_COMPATIBILITY.md)
- Dependency notes: [`docs/DEPENDENCIES.md`](./docs/DEPENDENCIES.md)
- Dagster ADR: [`docs/adr/ADR-007-dagster-eval-orchestration.md`](./docs/adr/ADR-007-dagster-eval-orchestration.md)
- Frozen OpenAPI snapshots:
  - `contracts/openapi/artifact_api.v1.json`
  - `contracts/openapi/thin_kb_api.v1.json`
- Normative file index: [`NORMATIVE_FILES.md`](./NORMATIVE_FILES.md)

## Phase 2 Endpoints

- `POST /v1/kb/ingest/document`: ingest file or inline document content into reviewable extract bundles
- `POST /v1/kb/ingest/code`: ingest file or inline code content with Python AST / optional Tree-sitter extraction
- `POST /v1/kb/search/hybrid`: search canonical Thin KB objects plus extracted chunks
- `POST /v1/kb/writeback/refine`: refine an `experience-packet.json` into candidate canonical objects

Optional Phase 2 dependencies can be installed with:

```bash
uv pip install '.[phase2]'
```

Wave 3 / Wave 4 dependencies can be installed with:

```bash
uv pip install '.[phase3]'
```

## Evaluation And Shadow Mode

- Frozen corpora live under `evals/datasets/gold/`, `evals/corpora/replay/`, and `evals/corpora/shadow/`
- Eval reports are written under `generated/reports/eval/<run_id>/`
- Shadow outputs are written under `generated/reports/shadow/<run_id>/`
- Dagster definitions live in `packages/core/pipeline/dagster_defs.py`

Run the frozen eval corpora directly:

```bash
.venv/bin/python scripts/generate_eval_report.py
```

Materialize the Dagster assets:

```bash
.venv/bin/python scripts/materialize_eval_assets.py --run-id nightly-smoke
```

Run the shadow pilot manifest:

```bash
.venv/bin/python scripts/run_shadow_pilot.py --run-id shadow-smoke
```

Compare two stored eval runs:

```bash
.venv/bin/python scripts/compare_eval_runs.py baseline-run candidate-run
```

## Thin KB Index Rebuild

Rebuild the manifest and FTS index from the JSON source of truth:

```bash
python -m packages.core.storage.thin_kb_store
```

## Recovery And Metrics

- Backup runbook: [`docs/RECOVERY_RUNBOOK.md`](./docs/RECOVERY_RUNBOOK.md)
- Observability notes: [`docs/OBSERVABILITY.md`](./docs/OBSERVABILITY.md)
- Evaluation notes: [`docs/EVALUATION.md`](./docs/EVALUATION.md)
- Shadow mode notes: [`docs/SHADOW_MODE.md`](./docs/SHADOW_MODE.md)
- Backup archive:
  - `.venv/bin/python scripts/backup_workspace.py --output backups/agent-foundation.tar.gz`
- Restore archive:
  - `.venv/bin/python scripts/restore_workspace.py --archive backups/agent-foundation.tar.gz --tasks-root restored/tasks --kb-root restored/kb`
- Metrics report:
  - `.venv/bin/python scripts/generate_metrics_report.py`
