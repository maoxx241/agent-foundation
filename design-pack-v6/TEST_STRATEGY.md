# TEST_STRATEGY

## Testing layers

### Unit tests
Cover:
- schema validation
- state transition validation
- filesystem storage helpers
- KB manifest/index sync logic

### API tests
Cover:
- task creation
- artifact CRUD
- invalid state changes
- Thin KB object CRUD/search

### E2E tests
Cover:
- full happy path through all task states
- blocked transition path
- OpenClaw adapter -> service call path

## Non-goals for Phase 1 tests
- no document parsing tests
- no embedding/vector search tests
- no graph relationship tests

## Required assertions

1. No illegal state transition is accepted.
2. No artifact write can bypass schema validation once the endpoint is wired.
3. `ExperiencePacket` finalization fails before `VALIDATED`.
4. Thin KB search returns only the requested object type.
5. Plugin tool input/output contracts match service contracts.
6. Memory integration is observed through explicit tool availability and successful recall/store behavior.

## Suggested fixtures
- one minimal project id
- one example task id
- one claim
- one procedure
- one case
- one decision


## Orthogonal matrix requirement

This package includes `ORTHOGONAL_TEST_MATRIX.md`.
Codex must implement the matrix in staged order:
- Artifact API matrix first
- Workflow gate matrix second
- Thin KB search matrix third
- Memory integration matrix fourth

Do not stop at happy-path tests.
At minimum, implement all A-* and W-* cases from the matrix.

## Recommended test tooling

- pytest for parametrized matrices
- hypothesis for schema and invariant fuzzing
- schemathesis for OpenAPI contract testing
- httpx for API integration tests
- pytest-asyncio when async endpoints need direct test clients
