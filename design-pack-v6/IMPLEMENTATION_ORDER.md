# IMPLEMENTATION_PLAN

This plan is intentionally operational. Codex should be able to implement directly from it.

## Goal

Deliver a working Phase 1 foundation with:
- OpenClaw orchestration
- Mem0-backed memory
- file-first artifact workflow
- thin canonical KB stub
- adapter plugin
- tests

## Milestone M1 — repository skeleton

Create a monorepo or two repos with this shape:

```text
agent-foundation/
  apps/
    artifact_api/
    thin_kb_api/
  libs/
    schemas/
    storage/
    services/
    utils/
  tasks/
  kb/
  tests/
  openclaw/
    plugin_adapter/
```

Exit criteria:
- repo boots
- lint/test commands exist
- no business logic yet

## Milestone M2 — shared schema layer

Implement:
- `schemas/common.py`
- `schemas/artifacts.py`
- `schemas/thin_kb.py`

Exit criteria:
- all models import cleanly
- examples validate
- JSON serialization is stable

## Milestone M3 — Artifact Store + state machine

Implement filesystem-backed artifact storage and stage transition validation.

Required capabilities:
- create task directory tree
- write artifact by stage/name
- read artifact by stage/name
- list artifacts for a task
- validate state transitions
- assemble task bundle summary

Exit criteria:
- create/read/write/list works
- invalid transitions fail server-side
- required file gates are enforced

## Milestone M4 — Artifact API

Implement FastAPI endpoints:
- `POST /v1/tasks`
- `GET /v1/tasks/{task_id}`
- `PATCH /v1/tasks/{task_id}/state`
- `GET /v1/tasks/{task_id}/bundle`
- `PUT /v1/tasks/{task_id}/artifacts/{stage}/{name}`
- `GET /v1/tasks/{task_id}/artifacts/{stage}/{name}`
- `GET /v1/tasks/{task_id}/artifacts`
- `POST /v1/tasks/{task_id}/experience/finalize`

Exit criteria:
- OpenAPI docs render
- all endpoints have tests

## Milestone M5 — Thin KB canonical store + SQLite FTS5

Implement canonical JSON object store for:
- `Claim`
- `Procedure`
- `Case`
- `Decision`

Implement a lightweight SQLite manifest/index with:
- object metadata table
- FTS5 virtual table for searchable text
- sync-on-write updates

Exit criteria:
- object write/read works
- simple search works by type/status/tags/text
- related lookup works

## Milestone M6 — Thin KB API

Implement endpoints:
- `POST /v1/kb/claims/search`
- `POST /v1/kb/procedures/search`
- `POST /v1/kb/cases/search`
- `POST /v1/kb/decisions/search`
- `GET /v1/kb/object/{id}`
- `GET /v1/kb/related/{id}`

Exit criteria:
- OpenAPI docs render
- tests cover search and lookup

## Milestone M7 — OpenClaw adapter plugin

Implement a thin TypeScript plugin that exposes:
- `artifact_create_task`
- `artifact_get`
- `artifact_put`
- `artifact_list`
- `artifact_update_state`
- `artifact_finalize_experience`
- `kb_search`
- `kb_get`
- `kb_related`

The plugin must not implement memory CRUD.
Mem0 plugin owns memory.

Exit criteria:
- plugin loads in OpenClaw
- tools call local services successfully

## Milestone M8 — Mem0 integration wiring

Tasks:
- configure `@mem0/openclaw-mem0`
- define `userId` / `runId` / project metadata conventions
- verify auto-recall and auto-capture
- verify explicit memory tool availability
- add a known-issues note about write-path observation

Exit criteria:
- cross-session memory recall works
- explicit `memory_*` tools work

## Milestone M9 — E2E tests

Required end-to-end flows:

### Flow A — happy path
- create task
- store EvidencePack
- design approved
- testspec frozen
- implementation artifacts written
- impl approved
- validation passed
- release artifacts written
- finalize ExperiencePacket

### Flow B — blocked transition
- attempt to move to IMPLEMENTED without TestSpec
- server rejects transition

### Flow C — plugin path
- OpenClaw tool call -> Artifact API -> persisted artifact
- OpenClaw tool call -> Thin KB API -> search result

Exit criteria:
- all three flows pass

## Milestone M10 — packaging and docs

Deliver:
- local run instructions
- environment variable docs
- example OpenClaw config fragment
- test commands
- troubleshooting notes

Exit criteria:
- another engineer can start the stack from docs alone
