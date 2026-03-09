# TODO_MASTER

This file replaces the earlier design-pack as the execution front page.
The project is assumed to have Phase 2 implemented:
- Memory Plane integrated
- Artifact Plane implemented
- Thin KB implemented
- Phase 2 stack integrated: Docling, Tree-sitter, LanceDB, Dagster

The next target is not “more features first”.
The next target is:

1. Stabilize the Phase 2 baseline
2. Build a serious evaluation and regression system
3. Run the system in shadow mode on real work
4. Turn the project into an AI-maintained engineering system

---

## P0. Freeze and stabilize Phase 2 baseline

### P0-1 API and schema freeze
- Freeze `artifact_api` request/response contracts
- Freeze `thin_kb_api` request/response contracts
- Freeze canonical object schemas for:
  - Claim
  - Procedure
  - Case
  - Decision
- Add compatibility policy for future schema evolution

Acceptance:
- Versioned API contracts exist
- Backward compatibility rules documented
- Contract tests exist for all public endpoints

### P0-2 State machine hardening
- Enforce legal state transitions only
- Reject invalid transitions with explicit errors
- Add idempotency rules for repeated operations
- Add rollback semantics for failed validation / failed writeback

Acceptance:
- Stateful tests cover all legal and illegal transitions
- Repeated calls do not corrupt task state

### P0-3 Recovery and backup
- Backup strategy for:
  - `tasks/`
  - `kb/canonical/`
  - memory backend config/state
  - LanceDB index data
- Restore drill runbook
- Corruption detection for manifest/index mismatch

Acceptance:
- Recovery drill can rebuild a clean environment from backup
- Restore is tested on a fresh machine or clean directory

### P0-4 Observability
- Structured logs for:
  - task creation
  - task state updates
  - writeback finalization
  - KB publish
  - recall / search failures
- Metrics for:
  - retrieval latency
  - retrieval hit@k
  - writeback promotion rate
  - validation fail rate
  - human intervention rate
- Trace IDs propagated from task -> API -> adapter -> worker

Acceptance:
- Logs are queryable by `task_id`
- Metrics dashboard or report script exists

---

## P1. Expand tests into a full orthogonal system

### P1-1 Contract testing
- OpenAPI-driven testing for Artifact API
- OpenAPI-driven testing for Thin KB API
- Negative tests for malformed payloads
- Schema evolution compatibility checks

### P1-2 Stateful and property testing
- Task workflow state machine
- Writeback invariants
- Thin KB object lifecycle invariants
- Manifest/index consistency invariants

### P1-3 Replay tests
- Replay real task bundles end-to-end
- Replay real retrieval queries against frozen corpora
- Replay real writeback promotion flows

### P1-4 Parsing / extraction tests
- Docling parsing determinism tests
- Tree-sitter extraction correctness tests
- Extract -> object mapping tests
- Parser failure handling tests

### P1-5 Retrieval tests
- Exact / FTS retrieval tests
- Hybrid retrieval tests
- Rerank tests
- Version/environment filtering tests
- Abstain behavior tests

### P1-6 Pipeline tests
- Dagster asset materialization tests
- Asset checks tests
- Partial recompute tests
- Publish pipeline tests

Acceptance:
- See `TEST_MATRIX_PHASE2_5.md`
- Minimum target: 120+ automated tests

---

## P2. Build an evaluation system

### P2-1 Gold datasets
Create frozen evaluation sets for:
- fact lookup
- how-to / procedure retrieval
- troubleshooting
- design/review evidence support
- writeback promotion

### P2-2 Ranking metrics
Track:
- hit@1
- hit@3
- hit@5
- MRR
- wrong-version rate
- false-positive rate
- abstain precision

### P2-3 Workflow metrics
Track:
- design acceptance rate
- review rejection rate
- validation failure rate
- writeback promotion rate
- human intervention rate
- regression escape rate

Acceptance:
- Evaluation report can be generated on demand
- Historical runs can be compared over time

---

## P3. Shadow-mode rollout on real work

### P3-1 Pilot tasks
- Choose 5–10 real tasks
- Run the system end-to-end in shadow mode
- Human remains the final approver

### P3-2 Intervention logging
For each intervention, capture:
- stage
- issue type
- severity
- fix type
- whether memory/KB/artifact was missing or wrong

### P3-3 Weekly review
- Review metrics
- Review failed retrievals
- Review weak writebacks
- Review test gaps

Acceptance:
- Shadow mode produces measurable quality data
- At least 2 weekly review cycles completed

---

## P4. Turn the project into an AI-maintained system

### P4-1 Add maintenance roles
- Maintainer Lead
- QA Steward
- Eval Steward
- Knowledge Steward
- Release Steward
- Infra Steward

### P4-2 Add recurring maintenance loops
- nightly replay + regression
- weekly retrieval eval
- weekly dependency review
- weekly KB audit
- release checklist generation

### P4-3 Add agent-facing operating docs
- repository README for agents
- role contracts
- change checklist
- release checklist
- rollback checklist

Acceptance:
- Another agent can enter the repo and operate with minimal human guidance
- Maintenance tasks can be delegated safely

---

## P5. Future work (only after P0–P4 are stable)
- richer graph relations
- graph-assisted retrieval
- stronger benchmark ingestion
- broader source ingestion
- UI/dashboard refinement
- multi-project federation

---

## Recommended immediate next sprint

Do these in order:
1. P0-1 API/schema freeze
2. P0-2 state machine hardening
3. P1-1 contract tests
4. P1-2 stateful/property tests
5. P2-1 gold datasets
6. P3-1 shadow mode pilot
