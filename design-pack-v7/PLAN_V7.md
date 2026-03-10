# PLAN_V7

## Objective

Turn the current Phase 2 implementation into a durable, AI-maintainable engineering substrate.

The next wave is not feature-first.
It is structure-first and reliability-first.

---

## Workstream 1: Normalize the repository

### Goals
- separate code root and state root
- eliminate duplicate normative docs/contracts
- make generated artifacts explicit
- make eval/replay first-class directories

### Deliverables
- new repository tree
- migration note from old tree to new tree
- single-source OpenAPI and schema directories
- clear code-vs-runtime boundary

---

## Workstream 2: Harden contracts and versioning

### Goals
- one source of truth for OpenAPI
- explicit schema versioning
- explicit object revisioning
- migration hooks for canonical objects

### Deliverables
- contract generation path
- schema version fields
- migration policy doc
- backward-compatibility tests

---

## Workstream 3: Add event/audit model

### Goals
- append-only task event log
- append-only KB event log
- promotion/deprecation auditability
- reconstructability from events + files

### Deliverables
- event schemas
- event writers in services
- event replay smoke tests
- audit queries / report script

---

## Workstream 4: Expand evaluation and replay

### Goals
- make replay a subsystem
- make retrieval eval measurable
- make workflow regression measurable

### Deliverables
- replay corpus layout
- gold datasets
- replay runner
- eval report generator
- CI gate on replay/eval

---

## Workstream 5: Operational hardening

### Goals
- backup/restore drill
- local auth/boundary policy
- structured logs and trace IDs
- health checks and diagnostics

### Deliverables
- backup script
- restore script
- health endpoints
- trace/log correlation
- runbooks

---

## Recommended sequencing

### Sprint O1 — Repo normalization
Focus:
- repository structure
- move docs/contracts
- remove duplicates
- add eval/fixtures/ops/migrations roots

### Sprint O2 — Contract consolidation
Focus:
- single-source OpenAPI
- generated artifacts path
- schema versioning
- compatibility tests

### Sprint O3 — Event ledger
Focus:
- task events
- kb events
- audit output
- replay from events smoke tests

### Sprint O4 — Replay/eval subsystem
Focus:
- replay corpus
- eval datasets
- retrieval metrics
- workflow regression reports

### Sprint O5 — Ops hardening
Focus:
- backup/restore
- health checks
- service auth/binding rules
- release/rollback runbooks

---

## Exit criteria for this wave

The optimization wave is complete when:
- code and runtime state are clearly separated
- public contracts have one source of truth
- every important mutation emits an event
- replay/eval exist as runnable subsystems
- CI can reject contract, replay, and retrieval regressions
