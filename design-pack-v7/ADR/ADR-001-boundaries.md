# ADR-001: Split into Memory Plane, Task Artifact Plane, and Thin KB Plane

## Status
Accepted

## Decision
The foundation is split into three planes:
- Memory Plane
- Task Artifact Plane
- Thin KB Plane

## Rationale
These solve different problems:
- Memory = what agents should remember
- Artifacts = what happened in this task
- Thin KB = what deserves long-term reuse

## Consequences
- OpenClaw does not become the canonical knowledge store
- task artifacts become the active workflow truth source
- knowledge promotion can be introduced later without breaking current behavior
