# ADR-003: Artifact store is filesystem-first

## Status
Accepted

## Decision
Task artifacts are stored as files under `tasks/<task_id>/...` and tracked in Git-friendly layouts.

## Rationale
- human-readable
- diffable
- reviewable
- rollback-friendly
- does not force a database before needed

## Consequences
- APIs become a thin layer over files
- schemas matter more than ORM convenience
- state machine checks file existence and validity directly
