# ADR-004: Thin KB uses file-first canonical objects with SQLite FTS5 index

## Status
Accepted

## Decision
Canonical Thin KB objects remain JSON files. Search/index in Phase 1 is implemented with SQLite + FTS5.

## Rationale
- P1 needs exact/text lookup more than semantic retrieval
- SQLite FTS5 is sufficient and operationally cheap
- file truth + local index keeps the system simple

## Consequences
- object writes must keep the index in sync
- rebuild command should exist
- LanceDB and embeddings are deferred to Phase 2
