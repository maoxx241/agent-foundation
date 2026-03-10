# Normative Files

This index defines the current source-of-truth files for public contracts, runtime layout, and core storage behavior.

## Normative

- `contracts/openapi/*.json`
- `contracts/jsonschema/*.json`
- `docs/API_COMPATIBILITY.md`
- `packages/core/config.py`
- `apps/artifact_api/main.py`
- `apps/thin_kb_api/main.py`
- `packages/core/schemas/`
- `packages/core/storage/`
- `packages/core/eval/`

## Non-Normative

- `generated/**`

`generated/` is disposable convenience output. Contract drift and compatibility gates are enforced against frozen snapshots under `contracts/`, not against files under `generated/`.
