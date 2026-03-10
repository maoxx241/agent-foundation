# API_CONTRACTS

## Artifact Service

### POST /v1/tasks
Create task workspace and initialize state.

Request body:
- `task_id`
- `project_id`
- `title`
- `goal`
- optional metadata

Response:
- task summary
- current state (`NEW`)

### GET /v1/tasks/{task_id}
Returns:
- task metadata
- current state
- available artifact summary

### PATCH /v1/tasks/{task_id}/state
Request body:
- `target_state`
- `changed_by`
- `reason`

Server behavior:
- validate current state
- validate required artifact gates
- update state atomically

### PUT /v1/tasks/{task_id}/artifacts/{stage}/{name}
Request body:
- arbitrary JSON or text depending on file type

Server behavior:
- validate stage/name
- validate payload if schema-backed object
- write atomically
- update task bundle metadata

### GET /v1/tasks/{task_id}/artifacts/{stage}/{name}
Returns exact stored artifact content.

### GET /v1/tasks/{task_id}/artifacts
List available artifacts grouped by stage.

### GET /v1/tasks/{task_id}/bundle
Return a flattened task bundle summary for routing/review.

### POST /v1/tasks/{task_id}/experience/finalize
Server behavior:
- require task state `VALIDATED` or stricter
- require `experience-packet.json`
- freeze writeback output

## Thin KB Service

### POST /v1/kb/claims/search
Search fields:
- query
- tags
- status
- scope
- limit

### POST /v1/kb/procedures/search
Same shape.

### POST /v1/kb/cases/search
Same shape plus optional env filters.

### POST /v1/kb/decisions/search
Same shape.

### GET /v1/kb/object/{id}
Return one canonical object.

### GET /v1/kb/related/{id}
Return directly related object ids and minimal metadata.

## Adapter tools

### Artifact tools
- `artifact_create_task`
- `artifact_get`
- `artifact_put`
- `artifact_list`
- `artifact_update_state`
- `artifact_finalize_experience`

### KB tools
- `kb_search`
- `kb_get`
- `kb_related`

### Memory tools
Provided by Mem0 plugin:
- `memory_search`
- `memory_list`
- `memory_store`
- `memory_get`
- `memory_forget`
