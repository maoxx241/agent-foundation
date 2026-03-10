# EXECUTION_PLAN

## Objective
Finish Phase 1 in one focused implementation pass without overbuilding.

## Milestone M1 — Data contracts and file layout

### Scope
- repository skeleton
- schemas
- directory creation helpers
- example payloads

### Exit criteria
- all schemas validate examples
- repository layout matches design

## Milestone M2 — Artifact Plane operational

### Scope
- artifact store
- task manifest
- state machine
- artifact API

### Exit criteria
- task creation works
- artifact round-trip works
- illegal transitions are blocked

## Milestone M3 — Thin KB operational

### Scope
- canonical object store
- metadata manifests
- SQLite FTS5 search
- Thin KB API

### Exit criteria
- all four object types can be written, read, searched
- related object lookup works

## Milestone M4 — OpenClaw integration and tests

### Scope
- adapter plugin
- Mem0 wiring
- e2e tests

### Exit criteria
- OpenClaw tool wrappers hit local services correctly
- happy-path lifecycle passes
- blocked finalize path fails cleanly

## Recommended sequencing

1. Finish M1 completely
2. Finish M2 completely
3. Finish M3 completely
4. Finish M4 completely

Do not parallelize aggressively unless tests remain stable.
