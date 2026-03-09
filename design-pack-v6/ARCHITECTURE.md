# agent-foundation / ARCHITECTURE

## 1. Objective

Build a small foundation layer that can be implemented first, reused across projects, and later
extended into a larger knowledge platform without breaking the initial workflow.

The design has three planes:

1. **Memory Plane**
   - Purpose: remember people, preferences, project context, recent decisions, and useful recurring facts.
   - Implementation strategy for Phase 1: use the Mem0 OpenClaw integration as the memory backend.
   - Important constraint: memory is not the long-term truth store for engineering artifacts.

2. **Task Artifact Plane**
   - Purpose: store the current task's explicit engineering artifacts.
   - This is the source of truth for the active workflow.
   - All stage gates operate on artifacts, not on chat history.

3. **Thin KB Plane**
   - Purpose: store a small amount of reusable, canonical knowledge.
   - Phase 1 only provides a thin shell and simple object store.
   - Full parsing, indexing, and graph-style retrieval are deferred to Phase 2+.

## 2. Why this split exists

### Memory Plane answers:
- What should the agent remember about the user?
- What recurring project facts should persist across sessions?
- What short-term context should survive session compaction or restart?

### Task Artifact Plane answers:
- What exactly happened in this task?
- What was designed?
- What was reviewed?
- What was tested?
- What was changed?
- What passed or failed?

### Thin KB Plane answers:
- Which knowledge is reusable beyond one task?
- Which conclusions are stable enough to be promoted?
- Which procedures and cases should become future reference material?

## 3. High-level system

```text
OpenClaw Work Plane
  ├─ lead
  ├─ knowledge
  ├─ engineer
  ├─ review
  ├─ qa
  └─ release
      │
      ├─ memory_*  -> Memory Plane (Mem0)
      ├─ artifact_* -> Artifact Service
      └─ kb_* -> Thin KB Service
```

OpenClaw is the orchestration and adapter layer, not the canonical knowledge layer.

## 4. Design principles

1. **Artifact-first workflow**
   - Conversation summaries are never the source of truth.
   - Stage advancement depends on explicit files and validated state transitions.

2. **Memory is not knowledge**
   - Memory is useful, but it is allowed to be compact, summarized, and user/project oriented.
   - Canonical engineering knowledge must be structured and reviewable.

3. **Tool-agnostic persistence**
   - Core data lives outside OpenClaw workspaces.
   - Future agent tools should be able to consume the same services.

4. **Git-friendly source of truth**
   - Task artifacts and canonical knowledge objects are stored as files.
   - File storage enables diff, rollback, backup, and easy local inspection.

5. **Thin first, rich later**
   - Phase 1 deliberately avoids heavy parsing and indexing infrastructure.
   - Later phases may add Docling, Tree-sitter, LanceDB, Dagster, and graph enrichment.

## 5. Phase 1 components

### 5.1 Memory Plane
Implemented by the Mem0 integration.
Responsibilities:
- long-term user memory
- project-shared memory
- session/task memory
- auto-recall / auto-capture
- explicit memory CRUD through tools

### 5.2 Artifact Service
A small API + local filesystem storage layer.
Responsibilities:
- create tasks
- store artifacts by stage
- enforce task state machine
- finalize writeback candidates

### 5.3 Thin KB Service
A small canonical store.
Responsibilities:
- persist reusable knowledge objects
- expose basic read/search interfaces
- receive promoted experience output later

## 6. Phase 1 object scope

### Memory objects
Not strongly typed like canonical KB objects. Main practical categories:
- user profile memory
- project profile memory
- recent working context
- remembered facts or preferences

### Artifact objects
Strongly typed:
- TaskBrief
- EvidencePack
- DesignSpec
- TestSpec
- PatchBundle
- ValidationReport
- ADR
- ExperiencePacket

### Thin KB objects
Only four kinds in Phase 1:
- Claim
- Procedure
- Case
- Decision

## 7. Task lifecycle

```text
NEW
-> EVIDENCE_READY
-> DESIGN_APPROVED
-> TESTSPEC_FROZEN
-> IMPLEMENTED
-> IMPL_APPROVED
-> VALIDATED
-> RELEASED
-> WRITTEN_BACK
```

Rollback rules:
- DESIGN_REJECTED -> DESIGN_APPROVED (previous valid stage remains authoritative)
- SELFTEST_FAILED -> IMPLEMENTED
- IMPL_REJECTED -> IMPLEMENTED
- VALIDATION_FAILED_BUG -> IMPLEMENTED
- VALIDATION_FAILED_SPEC -> DESIGN_APPROVED or TESTSPEC_FROZEN

## 8. Ownership model

### lead
- orchestrates the workflow
- does not write code
- does not directly edit trusted KB

### knowledge
- produces EvidencePack and GapReport
- does not design the final implementation
- does not approve artifacts

### engineer
- produces PatchBundle and SelfTestReport
- is the only role allowed to modify code in the main implementation workflow

### review
- design review mode
- implementation review mode
- does not rewrite production code

### qa
- test planning mode
- independent validation mode
- does not modify production code during validation

### release
- writes ADR / changelog / incident summary
- assembles writeback candidates
- does not directly promote knowledge into trusted canonical objects

## 9. Artifact storage model

Root:
```text
tasks/<task_id>/
```

Required structure:
```text
00_task/
10_evidence/
20_design/
30_test/
40_dev/
50_review/
60_validation/
70_release/
80_writeback/
```

Each stage contains named files with explicit schema or format.

## 10. Service contracts

### Memory tools
Handled by Mem0 integration:
- memory_search
- memory_store
- memory_get
- memory_list
- memory_forget

### Artifact tools
Provided by the custom adapter:
- artifact_create_task
- artifact_get
- artifact_put
- artifact_list
- artifact_update_state
- artifact_finalize_experience

### Thin KB tools
Provided by the custom adapter:
- kb_search
- kb_get
- kb_related

## 11. API boundaries

### Artifact Service
Owns:
- task creation
- artifact read/write
- state transitions
- task bundle assembly
- writeback finalization

### Thin KB Service
Owns:
- canonical object storage
- minimal object search
- relationship lookup
- future promotion endpoint

### OpenClaw Plugin Adapter
Owns:
- translating OpenClaw tool calls into backend HTTP requests
- auth/config handling
- thin, stateless request forwarding
- no business logic

## 12. Security and isolation

1. Memory isolation keys:
   - user_id
   - project_id
   - run_id / task_id

2. Artifact isolation:
   - every task gets its own directory
   - state transitions are validated server-side

3. Thin KB promotion:
   - no direct trusted write from agent roles
   - all promotion happens through explicit writeback rules

4. OpenClaw role isolation:
   - lead should be tool-starved
   - engineer should be the only code-writer in the main path
   - review and qa are read/validate roles

## 13. Phase plan

### Phase 1
- Mem0 integration
- Artifact Service
- Thin KB stub
- OpenClaw adapter plugin
- e2e flow for one task

### Phase 2
- Thin KB enrichment
- document/code ingestion
- exact search + hybrid retrieval
- richer writeback refinement

### Phase 3
- stronger indexing
- graph enrichment
- broader domain coverage
- larger automation surface

## 14. Acceptance criteria for Phase 1

1. A new task can be created.
2. EvidencePack can be written and read.
3. State transitions are validated.
4. Implementation cannot start before DesignSpec and TestSpec exist.
5. ExperiencePacket cannot be finalized before validation.
6. OpenClaw can call memory_* successfully.
7. OpenClaw can call artifact_* successfully.
8. OpenClaw can call kb_* successfully.
9. All artifact truth remains visible as local files.
10. Thin KB objects are persisted as reviewable files.

## 15. Explicit non-goals for Phase 1

- full RAG pipeline
- full parser stack
- semantic chunking engine
- vector database
- graph database
- graph-first retrieval
- full universal knowledge model
- automatic promotion of every task output into canonical knowledge

## 16. Recommended implementation order

1. schemas
2. artifact storage
3. artifact API
4. thin KB file store and API
5. OpenClaw adapter
6. Mem0 integration wiring
7. state machine enforcement
8. e2e tests
