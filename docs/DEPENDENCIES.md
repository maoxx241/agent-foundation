# Dependencies

## Runtime baseline

- Python `3.11`
- Node `22 LTS`

## Python extras

- `.[dev]`: pytest, hypothesis, schemathesis, Ruff, and Dagster test/runtime support
- `.[phase2]`: Docling, Tree-sitter, LanceDB
- `.[phase3]`: Dagster orchestration for eval and shadow-mode assets

## Phase 3 / 4 pin

- `dagster==1.12.18`

Rationale:

- matches the selected `design-pack-v6` version
- keeps orchestration local and file-first
- adds asset checks, retries, schedules, and lineage without changing public APIs
