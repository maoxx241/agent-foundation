# CODEX_OPTIMIZATION_HANDOFF

You are not starting from scratch.
Phase 2 is assumed complete.
Your job is to normalize and harden the project.

## Read first
1. REVIEW_FINDINGS_V7.md
2. REPO_OPTIMIZATION_V7.md
3. PLAN_V7.md
4. TODO_V7.md
5. AGENT_README.md

## Primary mission
Execute the next wave in this order:
1. remove duplicate sources of truth
2. normalize repository layout
3. split code root and state root
4. add versioning and event ledgers
5. make replay/eval first-class
6. harden ops and boundaries

## Non-goals
- do not add graph features yet
- do not expand object model aggressively
- do not move business logic into the OpenClaw adapter
- do not keep duplicate contract files alive

## First concrete deliverables
1. repository tree migration PR
2. normative contract consolidation PR
3. event ledger PR
4. replay/eval subsystem PR
5. ops hardening PR

## Definition of done for this wave
- one authoritative contract source exists
- code and runtime state are separated
- all critical mutations emit append-only events
- replay/eval can run automatically
- CI gates contract drift and replay regressions
