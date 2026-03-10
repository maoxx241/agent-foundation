# PHASE2_5_COMPONENT_MATRIX

| Plane | Component | Status | Keep / Change | Why |
|---|---|---|---|---|
| Orchestration | OpenClaw adapter | implemented | Keep | thin tool/routing layer |
| Memory | Mem0 integration | implemented | Keep | recall/capture already solved |
| Artifacts | filesystem + Git | implemented | Keep | diffable truth source |
| Thin KB canonical | file-first objects | implemented | Keep | portable and reviewable |
| Thin KB search | SQLite FTS5 | implemented | Keep for now | enough for current scale |
| Parsing | Docling | implemented | Keep | structured doc ingestion |
| Code extraction | Tree-sitter | implemented | Keep | symbol/config extraction |
| Retrieval | LanceDB | implemented | Keep | hybrid retrieval path |
| Pipeline | Dagster | implemented | Keep | asset graph + checks |
| Graph layer | none / optional | deferred | Keep deferred | not yet required |
| Metrics | partial/unknown | Add | needed for shadow mode |
| Replay corpus | partial/unknown | Add | needed for evaluation |
| Backup/restore | partial/unknown | Add | needed for reliability |
| Security tests | partial/unknown | Add | needed before wider use |
