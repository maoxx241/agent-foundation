# TESTING_STACK

Phase 1 testing stack:
- pytest: baseline test runner and parametrization
- pytest-asyncio: async endpoint tests
- httpx: API client integration tests
- hypothesis: property-based tests for schema and invariant coverage
- schemathesis: OpenAPI-driven contract fuzzing

Rationale:
- pytest gives simple fixture sharing and parametrized matrices
- Hypothesis covers invariant and edge-case spaces orthogonal matrices do not cover
- Schemathesis turns OpenAPI definitions into executable contract tests
