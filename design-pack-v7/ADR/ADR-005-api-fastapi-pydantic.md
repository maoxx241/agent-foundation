# ADR-005: FastAPI + Pydantic for service contracts

## Status
Accepted

## Decision
Use FastAPI for service endpoints and Pydantic v2 for all schemas.

## Rationale
- schema-first development
- low friction OpenAPI generation
- strong runtime validation
- straightforward tests

## Consequences
- endpoint contracts stay aligned with object schemas
- service code remains explicit and typed
