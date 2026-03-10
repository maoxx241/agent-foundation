# CODEX_V8_HANDOFF

You are continuing an existing project.
Do not restart architecture work.
Do not add flashy features first.

## Read first
1. REVIEW_V8.md
2. REPO_SHAPE_V8.md
3. PLAN_V8.md
4. TODO_V8.md
5. TEST_EXPANSION_V8.md
6. AGENT_SYSTEM_README_V2.md

## Primary mission

Make the project:
- operationally safer
- replayable
- evaluable
- easier for future agents to maintain correctly

## Priority order
1. contract unification and generation
2. service boundary hardening
3. append-only event ledgers
4. replay subsystem
5. retrieval/workflow eval subsystem
6. repo ergonomics for AI maintenance
7. backup/restore and observability

## Non-goals for this wave
- do not add graph retrieval yet
- do not add graph memory yet
- do not replace the thin KB search stack yet
- do not move business logic into the OpenClaw adapter
- do not treat passing unit tests as sufficient evidence

## Expected deliverables
- PR 1: contracts + generated artifacts + drift checks
- PR 2: service auth/boundary hardening
- PR 3: event ledgers and replay runner
- PR 4: retrieval/workflow eval and CI gates
- PR 5: backup/restore, observability, maintenance scripts

## Definition of done
- replay and eval are first-class and runnable
- critical mutations emit append-only events
- repo structure enforces more of the maintenance discipline
- another maintenance agent can continue with minimal hidden context
