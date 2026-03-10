# DEPENDENCIES

This document lists the **implementation dependencies Codex should pin** for Phase 1, plus the deferred stack for later phases.

## Runtime baseline

### Python
- **Python 3.11** preferred
- Python 3.12 acceptable

Rationale:
- Keeps compatibility simple across FastAPI, Pydantic v2, SQLModel, and future Phase 2 libraries.

### Node
- **Node.js 22 LTS** preferred for the OpenClaw adapter plugin

---

## Phase 1 required Python dependencies

### API / server
- `fastapi==0.135.1`
- `uvicorn[standard]==0.41.0`

### Schema / typing
- `pydantic==2.12.5`

### Testing / tooling
- `pytest==8.4.1`
- `httpx==0.28.1`
- `pyyaml==6.0.3`

### Optional, only if Codex needs local metadata tables
- `sqlmodel==0.0.37`

## Why SQLModel is optional

Phase 1 truth stores are file-first:
- task artifacts = filesystem
- canonical KB objects = filesystem JSON
- memory = Mem0 service

That means SQLModel is **not** a foundational dependency.
Use it only if Codex wants a small local manifest or audit table.

---

## Phase 1 required Node/OpenClaw dependencies

### Memory plane
- `@mem0/openclaw-mem0` (or the exact package you decide to install; verify package name during integration)

### Adapter plugin
- `typescript`
- `@types/node`

The adapter should otherwise minimize external dependencies.
Use native `fetch` and small utility code.

---

## Phase 1 built-in platform dependency

### SQLite with FTS5
Selected as the Thin KB search/index substrate.

Use cases in Phase 1:
- exact lookup
- keyword/full-text lookup
- tag/status/type filtering
- direct id lookup

Do **not** add sqlite vector search in Phase 1.

---

## Phase 2 deferred dependencies

### Document parsing
- `docling==2.77.0`

### Code parsing
- `tree-sitter==0.25.2`
- grammar packages as needed, e.g. `tree-sitter-python==0.25.0`

### Retrieval / indexing
- `lancedb==0.29.2`

### Pipeline orchestration
- `dagster==1.12.18`

---

## Explicitly not selected in Phase 1

- Qdrant
- Neo4j
- GraphRAG
- Unstructured
- Airflow
- Prefect
- Elasticsearch
- PostgreSQL as primary store

These may become valid later, but they are not justified by the current scope.
