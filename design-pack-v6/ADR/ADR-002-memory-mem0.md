# ADR-002: Use Mem0 for Phase 1 memory

## Status
Accepted

## Decision
Use `@mem0/openclaw-mem0` (or the exact verified package variant) as the memory backend for Phase 1.

## Rationale
- Provides Auto-Recall and Auto-Capture
- Exposes explicit memory CRUD tools
- Better matches the need for cross-session/cross-agent memory than workspace-only Markdown memory

## Consequences
- Memory backend is externalized
- OpenClaw custom plugin must not reimplement memory
- integration tests must observe actual store/recall behavior
