# AGENT README

This repository implements the foundation for an AI-operated engineering system.
It is designed so that multiple agents can safely reuse the same planes:

- Memory Plane
- Task Artifact Plane
- Thin KB Plane
- OpenClaw Adapter Plane

This README is written for agents, not for humans.

---

## 1. What this repository is

This repo is **not** a monolithic product app.
It is a reusable operating substrate for AI-led engineering workflows.

Its jobs are:
- remember relevant context
- store explicit task artifacts
- preserve reusable knowledge
- expose tools to orchestrators such as OpenClaw

---

## 2. What this repository is not

Do not treat this repo as:
- a generic chat memory dump
- a UI-first application
- a one-off project-specific codebase
- a place to improvise schemas on the fly

The system is contract-driven.

---

## 3. The planes

### Memory Plane
Purpose:
- user memory
- project memory
- session/task memory
- short/long-term recall

Primary rule:
- Memory stores context worth recalling later.
- Memory does **not** store canonical project truth.

### Task Artifact Plane
Purpose:
- current task source of truth
- explicit engineering workflow artifacts

Primary rule:
- If it happened in this task, it should be visible as an artifact.
- Do not replace artifacts with summaries in memory.

### Thin KB Plane
Purpose:
- store reusable, canonicalized knowledge

Canonical object types:
- Claim
- Procedure
- Case
- Decision

Primary rule:
- Thin KB is for reusable knowledge, not transient workflow state.

### OpenClaw Adapter Plane
Purpose:
- expose the system through tools and routes

Primary rule:
- Adapter should stay thin.
- Do not move business logic into the adapter unless absolutely necessary.

---

## 4. Repository mental model

Truth hierarchy:
1. current task artifacts
2. canonical KB objects
3. memory service recall
4. local notes / transient summaries

If sources conflict, prefer the higher layer in this hierarchy unless a validated migration rule says otherwise.

---

## 5. Main directories

- `apps/` service entrypoints
- `libs/` shared logic, schema, stores
- `tasks/` task artifacts
- `kb/canonical/` canonical thin KB objects
- `openclaw/` adapter/plugin docs and code
- `sql/` sqlite support files
- `tests/` automated test suite
- `ADR/` architectural decisions

---

## 6. How to make a change safely

When modifying this repo:

1. Identify which plane you are touching.
2. Check whether the change is:
   - schema
   - API contract
   - workflow/state machine
   - retrieval/indexing
   - adapter-only
3. Read the relevant ADR before changing behavior.
4. Update tests first or together with code.
5. Do not change canonical object meaning without migration notes.
6. If a change affects public contracts, update OpenAPI.
7. If a change affects workflow semantics, update the state machine docs.

---

## 7. Required invariants

Always preserve these invariants:

- illegal state transitions must fail explicitly
- writeback cannot finalize before validation
- canonical objects must remain schema-valid
- deprecated objects must not silently rank above trusted objects
- task-scoped artifacts must not leak across tasks
- memory scope boundaries must be respected
- adapter tools must not bypass service rules

---

## 8. Preferred development pattern

Use this pattern:
- small change
- tests first or alongside
- replay a real task if possible
- validate contracts
- validate state machine
- validate no boundary break

Avoid:
- broad refactors without tests
- mixing multiple planes in one change
- changing schemas and contracts casually
- adding new dependencies without an ADR

---

## 9. If you are Codex

You are expected to:
- execute implementation tasks in order
- preserve contracts
- add tests as a first-class deliverable
- leave clear migration notes for risky changes

Do not:
- silently rewrite the architecture
- collapse planes together
- bypass service boundaries for convenience

---

## 10. If you are a review agent

Review against:
- boundaries
- invariants
- test completeness
- contract stability
- migration safety
- rollback safety

---

## 11. If you are a maintenance agent

Your recurring jobs may include:
- nightly replay runs
- weekly retrieval eval
- weekly KB audit
- release checklist generation
- stale object detection
- regression triage

Keep maintenance actions explicit and logged.

---

## 12. Definition of done

A change is not done unless:
- contracts are consistent
- tests pass
- docs are updated if behavior changed
- state machine remains valid
- no plane boundary is weakened
