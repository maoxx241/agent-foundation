# CODEX_HANDOFF

You are implementing **Phase 1 only**.

## Build exactly this

1. Memory Plane through Mem0 plugin integration
2. Artifact Service
3. Thin KB stub with canonical objects + SQLite FTS5 search
4. OpenClaw adapter plugin
5. Tests

## Do not build

- parsing pipeline
- hybrid/vector retrieval
- graph layer
- universal KB promotion pipeline
- workflow scheduler beyond normal process startup

## Primary objective

Make the system runnable locally and reliable enough that the main engineering workflow can use:
- memory tools
- artifact tools
- basic kb tools

## Implementation rules

- Prefer simple, explicit code.
- Prefer file-first truth.
- Keep services thin.
- Keep plugin thinner.
- Validate all stage transitions server-side.
- Do not place canonical business state inside OpenClaw workspaces.

## Required output from Codex

- production-shaped but small codebase
- clear local startup docs
- tests that prove the happy path and blocked transition path
- an index rebuild command for Thin KB FTS if you implement a persistent SQLite index

## If you must choose

If there is a conflict between:
- richer infra vs smaller surface
- DB convenience vs file-first truth
- plugin intelligence vs service intelligence

Choose:
- smaller surface
- file-first truth
- service intelligence


## Testing is part of the deliverable

You must implement the orthogonal / pairwise matrices in `ORTHOGONAL_TEST_MATRIX.md`.
Minimum bar before completion:
- all A-* cases implemented
- all W-* cases implemented
- at least 3 K-* cases covering each query mode
- at least 3 M-* cases covering healthy / slow / unavailable backend
- Schemathesis smoke run wired for both OpenAPI files
- at least one Hypothesis test for state-machine invariants
