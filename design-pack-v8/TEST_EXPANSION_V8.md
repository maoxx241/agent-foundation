# TEST_EXPANSION_V8

## Goal

Move from "core tests pass" to "the system is difficult to regress silently".

This matrix expands Phase 2 tests into a more complete, long-lived quality system.

---

## Test families

### A. Contract tests

Purpose:
- verify API contracts match implementation
- detect backward-incompatible drift

Add:
- Schemathesis smoke for all endpoints
- negative tests for malformed payloads
- generated-contract drift tests

### B. State machine tests

Purpose:
- verify legal transitions and rollback behavior
- verify invalid transitions are blocked

Add:
- parameterized transition tests
- Hypothesis RuleBasedStateMachine for task lifecycle invariants

### C. Artifact correctness tests

Purpose:
- ensure artifact pathing, names, and write rules stay stable

Add:
- missing-stage tests
- overwrite behavior tests
- archive/move tests
- idempotent finalize tests

### D. Thin KB lifecycle tests

Purpose:
- verify create/update/promote/deprecate behavior
- verify provenance fields and revisioning

Add:
- candidate -> trusted promotion tests
- supersedes/deprecated_reason tests
- search visibility by status/scope/domain/version

### E. Event ledger tests

Purpose:
- ensure critical mutations always emit append-only events

Add:
- task transition emits event
- artifact write emits event
- KB promotion emits event
- replay run emits event
- event order and replayability checks

### F. Replay tests

Purpose:
- verify frozen real-world cases still behave within expected bounds

Add:
- at least 10 replay cases
- compare outputs against acceptance bands, not exact strings only
- regression report diff tests

### G. Retrieval eval tests

Purpose:
- detect ranking and scope/version regressions

Add:
- top-1/top-3/top-5 checks
- wrong-version regression checks
- abstain behavior checks
- domain/scope filter correctness

### H. Recovery tests

Purpose:
- verify backup/restore works in practice

Add:
- backup creates complete snapshot
- restore reconstructs state root
- replay/eval still run after restore

### I. Security / boundary tests

Purpose:
- ensure local-first assumptions remain true

Add:
- service binds to loopback by default
- unauthorized write rejected
- read endpoint accessible with correct token only
- cross-task and cross-project isolation tests

### J. Agent workflow tests

Purpose:
- ensure adapters and role workflows stay usable by AI agents

Add:
- OpenClaw adapter end-to-end tests
- maintenance-agent happy path
- review-agent read-only path
- release-agent writeback path

---

## Minimum target after this wave

- Contract tests: 20+
- State machine / property tests: 15+
- Artifact / Thin KB lifecycle tests: 25+
- Event ledger tests: 10+
- Replay tests: 10+
- Retrieval eval checks: 20+
- Recovery / security tests: 15+
- Agent workflow tests: 10+

Target total: **125–150 tests**, plus replay and eval corpora.

---

## Recommended stack

- `pytest`
- `pytest-asyncio`
- `httpx`
- `hypothesis`
- `schemathesis`

Use replay/eval corpora as first-class test assets, not as ad hoc fixtures.
