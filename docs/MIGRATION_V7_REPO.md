# V7 Repo Migration

This repository now follows the v7 normalization plan in three concrete ways:

1. Shared Python code moved from `libs/` to `packages/core/`.
2. Frozen corpora moved from `eval/` to `evals/`.
3. Runtime state defaults moved out of the source repo and now resolve from `AGENT_FOUNDATION_STATE_ROOT`.

## Path Mapping

- `libs/*` -> `packages/core/*`
- `eval/gold/*` -> `evals/datasets/gold/*`
- `eval/replay/*` -> `evals/corpora/replay/*`
- `eval/shadow/*` -> `evals/corpora/shadow/*`
- `reports/*` -> `generated/reports/*` by default
- `docs/ADR-007-dagster-eval-orchestration.md` -> `docs/adr/ADR-007-dagster-eval-orchestration.md`

## Runtime Defaults

- `AGENT_FOUNDATION_STATE_ROOT`
  - macOS default: `~/Library/Application Support/agent-foundation`
  - Linux default: `${XDG_STATE_HOME:-~/.local/state}/agent-foundation`
  - Windows default: `%LOCALAPPDATA%/agent-foundation`
- `AGENT_FOUNDATION_TASKS_ROOT`
  - default: `${STATE_ROOT}/tasks`
- `AGENT_FOUNDATION_KB_ROOT`
  - default: `${STATE_ROOT}/kb`
- `AGENT_FOUNDATION_OBSERVABILITY_ROOT`
  - default: `${STATE_ROOT}/observability`
- `AGENT_FOUNDATION_REPORTS_ROOT`
  - default: `generated/reports`

## Compatibility Notes

- `AGENT_FOUNDATION_EVAL_ROOT` is still accepted as a fallback, but `AGENT_FOUNDATION_EVALS_ROOT` is now preferred.
- Public HTTP contracts remain under `contracts/openapi/` and are still validated by contract snapshot tests.
