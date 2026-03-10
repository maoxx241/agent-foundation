# CODEX_MASTER_PROMPT

Use this as the initial implementation prompt for Codex.

---

You are implementing **Phase 1** of `agent-foundation`.

Your job is to build the following, and only the following:

1. Artifact Service
2. Thin KB Service (minimal)
3. OpenClaw adapter plugin
4. Mem0 integration wiring
5. End-to-end tests

Read these files first, in order:

1. `README.md`
2. `ARCHITECTURE.md`
3. `BOUNDARIES.md`
4. `COMPONENT_MATRIX.md`
5. `ADR_COMPONENT_SELECTION.md`
6. `STATE_MACHINE.md`
7. `API_CONTRACTS.md`
8. `DEPENDENCIES.md`
9. `IMPLEMENTATION_ORDER.md`
10. `IMPLEMENTATION_TASKS.md`
11. `schemas/common.py`
12. `schemas/artifacts.py`
13. `schemas/thin_kb.py`
14. `openclaw/PLUGIN_ADAPTER.md`
15. `openclaw/mem0_integration.md`

## Hard constraints

- Do not redesign the architecture.
- Do not add Docling, Tree-sitter, LanceDB, Dagster, graph DBs, or GraphRAG.
- Do not build a custom memory backend.
- Do not put business logic in the OpenClaw plugin.
- Keep task artifacts and canonical KB objects file-first and Git-friendly.
- Use SQLite FTS5 only for minimal Thin KB search.
- Treat SQLModel as optional; do not introduce it unless necessary.

## Implementation order

Follow work packages in `IMPLEMENTATION_TASKS.md` exactly.
Do not jump ahead to optional enhancements before the mandatory tests pass.

## Acceptance targets

- `POST /v1/tasks` works
- artifacts can be written and read
- illegal state transitions fail clearly
- `experience/finalize` is blocked until `VALIDATED`
- Thin KB supports create/read/search for Claim / Procedure / Case / Decision
- OpenClaw adapter exposes `artifact_*` and `kb_*`
- Mem0-backed memory tools are integrated, not reimplemented
- e2e tests cover one happy path and one blocked path

## Output style during implementation

- Make small, reviewable commits or commit-like checkpoints
- Keep code comments short and functional
- Prefer clear naming over clever abstractions
- Leave TODO markers only for Phase 2 work explicitly outside scope

---
