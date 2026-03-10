# Phase 1 schema notes

This folder adds executable schema drafts so Codex can start implementation immediately.

Files:
- `schemas/common.py`
- `schemas/artifacts.py`
- `schemas/thin_kb.py`

Implementation notes:
1. Keep canonical truth in task files and Thin KB JSON objects.
2. Use Mem0 for memory; do not reimplement a memory engine in Phase 1.
3. Keep Thin KB intentionally small: Claim / Procedure / Case / Decision only.
4. Keep OpenClaw as adapter/orchestrator only.

Suggested first implementation order:
1. `schemas/common.py`
2. `schemas/artifacts.py`
3. `apps/artifact_api`
4. `schemas/thin_kb.py`
5. `apps/thin_kb_api`
6. OpenClaw adapter plugin
