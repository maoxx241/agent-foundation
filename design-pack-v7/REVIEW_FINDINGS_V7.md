# REVIEW_FINDINGS_V7

This review assumes:
- Phase 2 implementation is complete
- Core Python tests pass
- The repository roughly follows the v6 design pack

This document focuses on structural defects, missing pieces, and what should be optimized next.

---

## Executive summary

The current version is **good enough to continue**, but it still looks like a strong prototype rather than a long-lived AI-maintained engineering substrate.

The biggest remaining gaps are:

1. **Too many sources of truth in docs/contracts**
2. **Code repo and mutable runtime data are not cleanly separated**
3. **Schema evolution and migration policy are underspecified in code-facing form**
4. **Observability / auditability is not yet first-class**
5. **Evaluation and replay are not yet equal to unit/API tests**
6. **Agent operating contracts are documented, but not yet enforced enough by repo structure and CI**

---

## A. Structural defects

### A1. Duplicate contract artifacts can drift

Current pack contains duplicates or near-duplicates such as:
- `api/*.yaml` and `openapi/*.yaml`
- `openclaw/PLUGIN_ADAPTER.md` and `openclaw/plugin_adapter.md`
- multiple plan/order/task files that overlap in purpose

This is a maintainability defect because AI agents and humans can edit different copies and silently introduce drift.

### A2. Documentation hierarchy is too flat

The root currently contains many equally important markdown files.
That is acceptable for a design pack, but weak for a long-lived implementation repo.
Agents will have to guess which file is normative.

### A3. Runtime data and source code are too close conceptually

The current design places `tasks/` and `kb/` next to application code.
That is workable for a prototype, but dangerous for a long-lived system because:
- runtime churn pollutes source control
- active task artifacts create noisy diffs
- CI and local development are harder to isolate
- replay/eval corpora and production-like runtime data become mixed

### A4. Thin KB lifecycle is present, but provenance is still too light

Current objects have `source_refs` and `related_ids`, but the following are still too implicit:
- object revision history
- schema version history
- promotion rationale
- migration traceability
- deprecation reason and supersession links

### A5. State machine is documented, but audit/event model is underdesigned

You already have task states and rollback rules.
What is still missing is an explicit append-only event ledger for:
- state transitions
- artifact writes
- writeback promotions
- KB object promotions / deprecations

Without an event ledger, debugging and AI maintenance become harder.

---

## B. Missing or underweighted capabilities

### B1. Config and environment policy

The repo needs a first-class configuration layer:
- environment profiles
- local-only defaults
- strict startup validation
- path policy for runtime roots
- memory backend / artifact API / KB API wiring

### B2. Auth / boundary policy for local services

Even if everything is local-first, the services should have explicit boundary rules:
- loopback-only binding by default
- lightweight service token or shared secret for adapters
- write APIs more restricted than read APIs
- explicit separation between operator and agent permissions where possible

### B3. Replay as a first-class subsystem

Replay is mentioned, but it should become its own subsystem with:
- corpus layout
- stable case IDs
- expected outputs / acceptance bands
- redaction strategy
- replay runner and report format

### B4. Evaluation assets are not yet structurally integrated

Gold datasets and retrieval evaluation are planned, but they need their own repo space and conventions.
They should not remain only as docs or TODOs.

### B5. CI/CD and release policy are still not concrete enough

You need a machine-readable pipeline definition that gates:
- schema changes
- API contract changes
- state machine changes
- replay regressions
- retrieval regressions

### B6. Agent-friendly enforcement is weaker than agent-friendly docs

There is already a good `AGENT_README.md`.
What is missing is stronger repository-enforced guidance:
- normative files directory
- generated vs hand-edited artifact boundaries
- make targets / scripts
- checklists embedded in CI

---

## C. Repo structure issues

### C1. `apps/` and `libs/` are fine, but not enough

For a long-lived AI-maintained repo, you also want dedicated top-level areas for:
- `contracts/`
- `evals/`
- `fixtures/`
- `ops/`
- `scripts/`
- `migrations/`
- `agents/`

### C2. `tasks/` should not live in the source repo by default

Recommended change:
- keep **code** in the source repo
- move **mutable runtime state** to a separate state root or separate repo

### C3. `kb/canonical/` may need split treatment

Recommended split:
- `kb/canonical/` for curated/promoted long-lived knowledge
- `runtime/kb_inbox/` or `state/kb_candidates/` for newly generated/promoted-but-not-final material

### C4. Generated artifacts need explicit homes

Add:
- `generated/openapi/`
- `generated/schemas/`
- `generated/reports/`

This reduces confusion between source files and generated files.

---

## D. Highest-value optimizations

### D1. Introduce a dual-repo or dual-root model

**Code root**
- source code
- schemas
- contracts
- tests
- eval harness
- docs

**State root**
- active tasks
- archived tasks
- canonical KB data
- indexes
- replay corpora
- backups
- audit ledgers

### D2. Make one OpenAPI source authoritative

Generate all exported OpenAPI artifacts from a single source.
Do not keep two hand-maintained copies.

### D3. Add explicit versioning fields everywhere they matter

At minimum add:
- `schema_version`
- `api_version`
- `object_revision`
- `supersedes`
- `deprecated_reason`

### D4. Add append-only event ledgers

Use append-only ledgers for:
- task state transitions
- artifact writes
- KB promotions
- recall/search failures if useful

### D5. Promote replay/eval to first-class directories

The project should treat replay and eval as core product infrastructure, not an afterthought.

---

## E. What not to do next

Do **not** do these yet:
- add GraphRAG / Neo4j now
- widen the object model aggressively
- move business logic into the OpenClaw adapter
- overfit to one current project domain
- add many new infra dependencies before CI/replay are stable

---

## Final recommendation

Next optimization wave should focus on:

1. repo normalization
2. contract/source-of-truth consolidation
3. event/audit model
4. replay/eval integration
5. CI/release hardening

Only after that should you move to richer retrieval or graph-based capabilities.
