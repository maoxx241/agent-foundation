# ADR-006: Defer parsing, hybrid retrieval, and graph enrichment

## Status
Accepted

## Decision
Do not include Docling, Tree-sitter, LanceDB, Dagster, or property-graph infrastructure in Phase 1.

## Rationale
Phase 1 is about operational correctness and workflow truth, not ingestion richness.

## Consequences
- P1 implementation is smaller and faster
- P2 has a clean upgrade path
- current design pack must leave room for later adapters without depending on them now
