# COMPONENT_SELECTION_NOTES

## Why SQLite FTS5 in Phase 1

Phase 1 queries are dominated by:
- exact ids
- tags/status filters
- hard tokens like versions, paths, config names, error signatures

That means FTS5 provides enough value without introducing embeddings or vector infrastructure.

## Why no SQLModel by default

There are too few truly relational requirements in Phase 1.
Canonical truths live in files.
Add SQLModel only if Codex finds a concrete need for a local registry table.

## Why no LanceDB yet

LanceDB is a strong Phase 2 candidate because it supports vector, full-text, and hybrid search.
But P1 should optimize for operational correctness before retrieval richness.

## Why no Docling / Tree-sitter yet

They solve ingestion quality, not foundation correctness.
The system first needs a clean place to put knowledge before it needs richer extraction.
