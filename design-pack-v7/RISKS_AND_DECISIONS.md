# RISKS_AND_DECISIONS

## High-confidence decisions
- Memory is externalized via Mem0.
- Task artifacts are file-first and state-machine governed.
- Thin KB is file-first with SQLite FTS5 indexing.
- OpenClaw only adapts and orchestrates.

## Main Phase 1 risks

### 1. Memory write-path surprises
Risk:
- Mem0 auto-capture behavior may not match expectations under all plugin flows.
Mitigation:
- lock plugin version
- add observed integration tests
- keep manual memory tools available

### 2. Artifact state drift
Risk:
- prompts or tool misuse attempt to advance state before required files exist.
Mitigation:
- server-side transition validation only
- artifacts checked before every state promotion

### 3. KB/search mismatch
Risk:
- canonical files and SQLite FTS index drift out of sync.
Mitigation:
- update index synchronously on object write/delete
- add index rebuild command
- add consistency check test

### 4. Overbuilding too early
Risk:
- Phase 1 expands into parsing/retrieval/graph work.
Mitigation:
- explicit scope guard: no Docling, Tree-sitter, LanceDB, Dagster, graph in Phase 1
