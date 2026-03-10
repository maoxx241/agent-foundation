# AGENT_SYSTEM_README_V2

## What this repository is

This repository is not just an app.
It is an AI-maintained engineering substrate with three planes:

1. **Memory Plane** — user/project/session memory via Mem0
2. **Task Plane** — explicit task artifacts and workflow state
3. **Thin KB Plane** — reusable canonical knowledge objects

OpenClaw is the orchestration and adapter layer.
It is not the source of truth for memory, artifacts, or knowledge.

---

## Source-of-truth order

When working on this project, use this order:

1. `contracts/` — normative API/schema/event contracts
2. `packages/core/schemas/` — canonical code models
3. `docs/adr/` — architecture decisions
4. `agents/role_contracts/` — role-specific operational rules
5. `tests/` and `evals/` — behavioral truth and quality guardrails

Do not treat generated files, transient runtime data, or random markdown notes as primary truth.

---

## Repository boundaries

### Code root
Contains implementation, contracts, tests, evals, docs, scripts.

### State root
Contains active tasks, KB data, indexes, ledgers, replay captures, backups.

### Workspace root
Contains transient worktrees and scratch spaces for agents.

Never write active runtime data into the code root.

---

## If you are a coding agent

### You may
- modify implementation under `apps/`, `packages/`, `scripts/`, `ops/`
- update normative contracts only when the code and tests require it
- add tests and eval assets
- add migrations when schemas change

### You must not
- invent a second source of truth
- bypass replay/eval when changing workflow or retrieval behavior
- edit generated files as the authoritative source
- write runtime state into the code repository

---

## Required workflow for non-trivial changes

1. read the relevant ADRs and contracts
2. identify which plane is affected: memory / task / thin-kb / adapter / ops
3. update code
4. update tests
5. update replay/eval assets if behavior changes
6. regenerate derived contracts if needed
7. run local validation
8. summarize migration or rollback impact

---

## Required workflow for schema or contract changes

1. update Pydantic models
2. update normative contracts
3. generate derived contracts
4. add migration if needed
5. add contract drift and backward-compat tests
6. update replay/eval acceptance bands if behavior intentionally changes

---

## Required workflow for maintenance agents

Maintenance agents should prefer:
- narrow PRs
- event-emitting changes
- replay/eval before broad refactors
- migration-backed changes over silent rewrites

If unsure, optimize for:
- traceability
- reversibility
- bounded blast radius
