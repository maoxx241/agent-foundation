# IMPLEMENTATION_TASKS

This is the work breakdown structure Codex should follow.
The order is intentional.

## WP-1 Repository skeleton

### Deliverables
- `apps/artifact_api/`
- `apps/thin_kb_api/`
- `libs/schemas/`
- `libs/storage/`
- `openclaw/plugin_adapter/`
- `tasks/`
- `kb/`
- `tests/`

### Done when
- repository layout matches `DIRECTORY_LAYOUT.md`
- apps and libs import cleanly

## WP-2 Core schemas

### Deliverables
- implement `common.py`
- implement `artifacts.py`
- implement `thin_kb.py`
- add schema self-tests

### Done when
- every schema validates example payloads
- JSON serialization is deterministic
- schema tests pass

## WP-3 Artifact storage layer

### Deliverables
- file-backed artifact store
- stage path resolution helpers
- task manifest creation
- state.json handling
- write/read/list APIs at library level

### Done when
- creating a task creates the full directory tree
- writing an artifact stores it in the correct stage path
- listing returns accurate stage/file metadata

## WP-4 Artifact state machine

### Deliverables
- legal state transition validator
- rollback validator
- task bundle assembler

### Done when
- illegal transitions are rejected
- legal transitions are accepted
- bundle API returns coherent task snapshot

## WP-5 Artifact API

### Deliverables
- `POST /v1/tasks`
- `GET /v1/tasks/{task_id}`
- `PATCH /v1/tasks/{task_id}/state`
- `PUT /v1/tasks/{task_id}/artifacts/{stage}/{name}`
- `GET /v1/tasks/{task_id}/artifacts/{stage}/{name}`
- `GET /v1/tasks/{task_id}/artifacts`
- `GET /v1/tasks/{task_id}/bundle`
- `POST /v1/tasks/{task_id}/experience/finalize`

### Done when
- OpenAPI docs render
- happy-path manual curl test passes
- blocked transition path returns a clear 4xx error

## WP-6 Thin KB storage layer

### Deliverables
- file-backed canonical object store
- object validation on write
- metadata manifest
- SQLite FTS5 index builder/searcher

### Done when
- all four object types can be created and read
- exact text search returns correct objects
- tag filtering works

## WP-7 Thin KB API

### Deliverables
- `POST /v1/kb/claims/search`
- `POST /v1/kb/procedures/search`
- `POST /v1/kb/cases/search`
- `POST /v1/kb/decisions/search`
- `GET /v1/kb/object/{id}`
- `GET /v1/kb/related/{id}`

### Done when
- search supports exact text + metadata filters
- get/related endpoints resolve canonical objects consistently

## WP-8 OpenClaw adapter plugin

### Deliverables
- artifact tool wrappers
- kb tool wrappers
- HTTP client config
- clear error translation for agent tools

### Done when
- OpenClaw can invoke all required artifact_* and kb_* tools
- plugin contains no business logic

## WP-9 Mem0 wiring

### Deliverables
- install/config notes reflected in example config
- smoke tests for memory recall/store
- integration readme

### Done when
- memory tools are available through the configured plugin
- one cross-session memory retrieval test passes

## WP-10 End-to-end tests

### Deliverables
- happy-path task lifecycle test
- illegal transition test
- writeback finalize guard test
- OpenClaw adapter smoke test

### Done when
- a task can move from NEW to WRITTEN_BACK in tests
- finalize fails before VALIDATED
- tool wrappers can round-trip against local APIs
