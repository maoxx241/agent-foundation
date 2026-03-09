# COMPONENT_MATRIX

This matrix captures **Phase 1 selections**, **alternatives considered**, and **why each choice was made**.

| Area | Selected component | Decision level | Phase | Why selected | Alternatives considered | Rejected now because |
|---|---|---:|---:|---|---|---|
| Agent orchestration / interface | OpenClaw plugin adapter | Locked | P1 | OpenClaw plugins can register HTTP routes, agent tools, CLI commands, and background services; this is exactly the right abstraction for forwarding `artifact_*` and `kb_*` tools. | Direct SDK coupling; custom gateway | Increases lock-in or reimplements what OpenClaw already provides |
| Agent memory | `@mem0/openclaw-mem0` | Locked | P1 | Provides Auto-Recall, Auto-Capture, and explicit memory tools; memory becomes a dedicated service instead of ad hoc workspace files. | OpenClaw built-in memory only; custom memory service | Built-in memory is workspace-centric and file-first, useful but not sufficient for the desired cross-session/cross-agent substrate |
| API framework | FastAPI | Locked | P1 | Type-driven API design, strong validation, straightforward OpenAPI generation, low ceremony | Flask, Litestar, Starlette only | Lower leverage for schema-first delivery |
| Schema layer | Pydantic v2 | Locked | P1 | Single source of truth for request/response/body models and canonical object definitions | Dataclasses + custom validation | More boilerplate, weaker JSON Schema leverage |
| Artifact truth store | Filesystem + Git | Locked | P1 | Diffable, human-readable, reviewable, easy rollback, no DB-first complexity | PostgreSQL-first, object-store-first | Unnecessary operational burden for current scope |
| Artifact registry | None mandatory; derive from filesystem | Locked | P1 | Keep P1 simple. State lives in files. | SQLModel/SQLite manifest | Optional later; do not block P1 |
| Thin KB canonical storage | Filesystem JSON | Locked | P1 | Same reasons as artifacts: Git-friendly, reviewable, portable | SQLite-only canonical store | Harder to inspect/edit/review directly |
| Thin KB search/index | SQLite + FTS5 | Locked | P1 | Supports exact/full-text search over canonical objects with low complexity and no extra infra | LanceDB, Qdrant, Elasticsearch | Too early; P1 does not need embeddings |
| Optional metadata ORM | SQLModel | Optional | P1 | Useful if Codex wants a local task registry or audit manifest | Raw SQLAlchemy | More code for no strong gain in P1 |
| Doc parsing | Docling | Deferred | P2 | Strong candidate for unified parsing of PDF/DOCX/HTML/etc. and structured export | Unstructured, custom parsers | No need to block P1 |
| Code parsing | Tree-sitter | Deferred | P2 | Incremental parsing and CST extraction for repo knowledge | regex/grep, LSP indexing | Not required before P2 extraction pipeline |
| Hybrid retrieval | LanceDB | Deferred | P2 | Native vector + FTS + rerank path for later KB growth | Qdrant, pgvector | P1 can be handled by exact + tags + FTS |
| Data orchestration | Dagster | Deferred | P2 | Asset graph maps naturally to source->extract->object->view->index | Airflow, Prefect, scripts | P1 has no complex ingestion graph |
| Graph enrichment | LlamaIndex PropertyGraph / Neo4j | Deferred | P3 | Useful only when relationship-first queries become common | none | Premature for P1 |

## Phase 1 hard choices

### Locked selections
- OpenClaw plugin adapter
- Mem0 plugin
- FastAPI
- Pydantic
- Filesystem + Git for artifacts
- Filesystem JSON + SQLite FTS5 for Thin KB

### Optional in Phase 1
- SQLModel

### Explicitly delayed
- Docling
- Tree-sitter
- LanceDB
- Dagster
- Property graph / Neo4j / GraphRAG
