# OPENCLAW_INTEGRATION

## Scope

OpenClaw is not the canonical data store.
OpenClaw is the **orchestration and adapter layer**.

## Plugin responsibilities

The custom plugin should:
- expose agent tools for Artifact and Thin KB services
- optionally expose health-check HTTP routes
- avoid business logic duplication

The custom plugin should not:
- store canonical task artifacts itself
- store canonical KB objects itself
- implement a memory backend

## Memory integration

Use Mem0 plugin for memory.
The custom plugin must not wrap or duplicate `memory_*` tools.

## Tool surface

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

## Suggested plugin config

The custom plugin should accept:
- `artifactApiBaseUrl`
- `thinKbApiBaseUrl`
- `requestTimeoutMs`

## Error handling

Tool results should be normalized into:
- `ok: true/false`
- `error_code`
- `message`
- `data`

Do not leak raw stack traces to the LLM.
