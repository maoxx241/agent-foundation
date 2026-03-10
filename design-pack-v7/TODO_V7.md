# TODO_V7

## P0 — Must do first

### P0-1 Consolidate sources of truth
- [ ] Choose **one** normative OpenAPI directory
- [ ] Delete or deprecate the duplicate OpenAPI directory
- [ ] Choose **one** normative OpenClaw adapter spec file
- [ ] Delete or deprecate duplicate plugin spec docs
- [ ] Add a `NORMATIVE_FILES.md` index

Acceptance:
- No duplicated normative contract files remain
- A new agent can identify the authoritative files in under 2 minutes

### P0-2 Normalize repository structure
- [ ] Refactor `libs/` into `packages/core/`
- [ ] Create `contracts/`, `evals/`, `fixtures/`, `ops/`, `migrations/`, `generated/`, `agents/`
- [ ] Move ADRs under `docs/adr/`
- [ ] Add migration notes for the tree rewrite

Acceptance:
- New repo tree matches `REPO_OPTIMIZATION_V7.md`
- Existing tests still pass after relocation

### P0-3 Split code root from state root
- [ ] Define `STATE_ROOT` config
- [ ] Move `tasks/` out of the source repo working tree
- [ ] Move `kb/canonical/` or at least active candidate data out of code root
- [ ] Document local dev and CI path conventions

Acceptance:
- Source repo no longer churns when running normal tasks
- Runtime state can be wiped/recreated independently

---

## P1 — Contracts and versioning

### P1-1 Add schema and object versioning
- [ ] Add `schema_version` to canonical objects
- [ ] Add `artifact_version` or `artifact_schema_version` where needed
- [ ] Add `object_revision` to Thin KB objects
- [ ] Add `supersedes` / `deprecated_reason` fields where applicable

Acceptance:
- Objects and artifacts can evolve without silent ambiguity

### P1-2 Generate contracts
- [ ] Generate JSON Schema from Pydantic models into `generated/schemas/`
- [ ] Generate OpenAPI from service code or a single contract source into `generated/openapi/`
- [ ] Add tests that fail on contract drift

Acceptance:
- Hand-maintained contract duplication is removed

---

## P2 — Event/audit subsystem

### P2-1 Task event ledger
- [ ] Create event schemas for task lifecycle
- [ ] Emit events for state transition, artifact write, finalize experience
- [ ] Store append-only task event log under state root

### P2-2 KB event ledger
- [ ] Create event schemas for create/update/promote/deprecate
- [ ] Emit events for KB mutations and promotions
- [ ] Store append-only KB event log under state root

### P2-3 Audit tooling
- [ ] Add simple event reader/query tool
- [ ] Add audit report script by `task_id` and `object_id`

Acceptance:
- Important changes can be reconstructed from event logs

---

## P3 — Replay and evaluation

### P3-1 Replay subsystem
- [ ] Create `evals/corpora/replay/`
- [ ] Define replay case manifest schema
- [ ] Add replay runner CLI
- [ ] Add baseline replay report format

### P3-2 Retrieval eval
- [ ] Create gold datasets for fact/how-to/troubleshooting/design/validation
- [ ] Add metrics: hit@1/3/5, MRR, wrong-version rate, abstain precision
- [ ] Add regression threshold config

### P3-3 Workflow eval
- [ ] Track design acceptance rate
- [ ] Track review rejection rate
- [ ] Track validation failure rate
- [ ] Track writeback promotion rate
- [ ] Track human intervention rate

Acceptance:
- Replay and eval run in CI or nightly automation

---

## P4 — Operational hardening

### P4-1 Backup/restore
- [ ] Backup task state root
- [ ] Backup KB canonical + ledgers + indexes
- [ ] Add restore script
- [ ] Add restore drill test

### P4-2 Service boundary hardening
- [ ] Bind services to loopback by default
- [ ] Add lightweight service token/shared secret between adapter and backend
- [ ] Separate read and write permissions in config if practical

### P4-3 Observability
- [ ] Structured logging with `task_id`, `request_id`, `trace_id`
- [ ] Health endpoints for services
- [ ] Metrics/report scripts for API latency, retrieval latency, promotion counts

Acceptance:
- A failed run can be diagnosed from logs and events without manual guesswork

---

## P5 — Test expansion

### P5-1 Contract and property tests
- [ ] Add Schemathesis contract suite
- [ ] Add Hypothesis state machine suite
- [ ] Add object lifecycle invariants

### P5-2 Replay tests
- [ ] Add replay tests under `tests/replay/`
- [ ] Add at least 10 frozen real-world replay cases

### P5-3 Security/boundary tests
- [ ] Service binding tests
- [ ] unauthorized write attempt tests
- [ ] cross-task isolation tests
- [ ] memory scope leak tests

Acceptance:
- Test suite covers correctness, contracts, replay, and boundary behavior

---

## P6 — Agent operating model

### P6-1 Agent contracts as code-adjacent docs
- [ ] Move/expand `AGENT_README.md` into `agents/`
- [ ] Add role-specific contracts for:
  - Codex implementer
  - review agent
  - QA/eval agent
  - maintenance agent

### P6-2 Maintenance loops
- [ ] Add nightly replay script
- [ ] Add weekly retrieval eval script
- [ ] Add stale object audit script
- [ ] Add release checklist generator

Acceptance:
- Another agent can safely continue development with minimal human context
