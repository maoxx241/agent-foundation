# ADR_COMPONENT_SELECTION

## ADR-001 — OpenClaw is the control plane, not the knowledge plane

### Status
Accepted

### Context
OpenClaw agents need access to memory, task artifacts, and thin knowledge. But the long-term goal is tool portability and domain portability.

### Decision
OpenClaw will remain an orchestration and adapter layer only.
Canonical data will live outside OpenClaw workspaces.

### Consequences
- plugin tools become thin wrappers over HTTP services
- OpenClaw memory does not become the system of record
- future agent frontends can reuse the same services

---

## ADR-002 — Mem0 is selected for the Memory Plane

### Status
Accepted

### Context
Phase 1 needs persistent memory with automatic recall/capture and explicit memory CRUD. Rebuilding a memory backend would add delay and risk.

### Decision
Use `@mem0/openclaw-mem0` as the Memory Plane.
Do not build a custom memory backend in Phase 1.

### Consequences
- memory behavior is delegated to Mem0
- project effort focuses on artifacts and thin KB
- memory write/read behavior must be validated with integration tests

### Risks
- plugin regressions or recall/capture edge cases

### Mitigations
- pin plugin version
- add memory integration smoke tests
- keep memory usage narrow: preferences, context summaries, recurring facts

---

## ADR-003 — Artifact Plane is filesystem-first

### Status
Accepted

### Context
The active engineering workflow requires explicit stage artifacts that can be diffed, reviewed, and versioned.

### Decision
Use the local filesystem as the source of truth for task artifacts, with Git-friendly layouts.

### Consequences
- humans can inspect state directly
- rollback and diff are straightforward
- APIs become a convenience layer over files, not the truth source

---

## ADR-004 — Thin KB is object-first and minimal in Phase 1

### Status
Accepted

### Context
The long-term direction is a reusable knowledge platform, but Phase 1 should not overbuild retrieval or parsing.

### Decision
Thin KB will only support four canonical objects in Phase 1:
- Claim
- Procedure
- Case
- Decision

### Consequences
- knowledge remains reusable without forcing a full platform build
- cards, graph views, and richer indices are deferred

---

## ADR-005 — SQLite FTS5 is selected over vector retrieval in Phase 1

### Status
Accepted

### Context
Phase 1 Thin KB will be small. Most early queries will be exact-match, tag-filtered, version-sensitive, or simple troubleshooting lookups.

### Decision
Use SQLite FTS5 with metadata filters for the first search implementation.
Do not add LanceDB/Qdrant/vector retrieval in Phase 1.

### Consequences
- lower complexity
- deterministic search behavior for exact technical terms
- semantic search is deferred until there is enough data to justify it

---

## ADR-006 — SQLModel is optional, not foundational

### Status
Accepted

### Context
Earlier drafts included SQLModel as a baseline dependency. After review, Phase 1 does not require a DB-first metadata layer.

### Decision
Do not make SQLModel a mandatory Phase 1 dependency.
Allow Codex to introduce it only if task registry / audit metadata become painful to maintain with plain manifests.

### Consequences
- simpler first pass
- easier local deployment
- fewer moving parts
