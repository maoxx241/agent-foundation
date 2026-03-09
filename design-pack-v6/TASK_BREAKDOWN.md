# TASK_BREAKDOWN

This is the task list Codex should execute in order.

## 1. Repo bootstrap
- create Python package layout
- create plugin package layout
- create `tasks/` and `kb/` roots
- add `.gitignore`, formatters, test config

## 2. Core schema implementation
- implement common enums and base models
- implement artifact models
- implement Thin KB models
- add schema tests

## 3. Artifact storage layer
- create task directory initializer
- implement atomic file write helper
- implement artifact read/list helpers
- implement task state read/write
- implement stage gate validator
- implement bundle builder

## 4. Artifact API
- wire FastAPI app
- route: create task
- route: get task
- route: patch task state
- route: put artifact
- route: get artifact
- route: list artifacts
- route: get bundle
- route: finalize experience

## 5. Thin KB storage layer
- create canonical object path conventions
- implement object read/write
- implement SQLite metadata db
- implement FTS5 virtual table
- implement sync-on-write indexing
- implement related object lookup

## 6. Thin KB API
- search routes per object type
- object lookup route
- related route

## 7. OpenClaw adapter plugin
- implement config for API base URL
- implement artifact tools
- implement kb tools
- register tool schemas
- add smoke tests if practical

## 8. Mem0 integration
- add plugin installation/config notes
- ensure no duplicate memory tool shims in custom plugin
- verify `userId` and `runId` conventions

## 9. E2E tests
- happy path
- blocked transition
- plugin-to-service path

## 10. Packaging
- `pyproject.toml`
- requirements lock or pinned deps file
- plugin `package.json`
- run scripts / make targets
