# API Compatibility Policy

This repository treats the current public HTTP surface as `v1`.

Frozen contracts live in:

- `contracts/openapi/artifact_api.v1.json`
- `contracts/openapi/thin_kb_api.v1.json`

Compatibility rules for `v1`:

- Existing paths and HTTP methods are stable unless there is an explicit migration note.
- Existing required request fields must not be removed or renamed.
- Existing response fields must not change meaning.
- New response fields may be added only when they are optional and additive.
- New request fields may be added only when they are optional and ignored safely by older callers.
- Error semantics should remain explicit:
  - `404` for missing task/object
  - `409` for workflow or lifecycle conflicts
  - `422` for request/schema validation failures
  - `400` for service-level invalid Phase 2 operations

Change process:

1. Update implementation.
2. Update or add tests.
3. Regenerate the matching OpenAPI snapshot deliberately.
4. Document any migration or compatibility note in the changelog / release notes.

Schema evolution rules:

- Canonical KB objects (`Claim`, `Procedure`, `Case`, `Decision`) are append-only for non-breaking fields.
- Artifact schemas are append-only for non-breaking fields.
- Field removals, semantic repurposing, or enum narrowing require a version bump or migration note.
