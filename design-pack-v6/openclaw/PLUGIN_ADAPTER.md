# OpenClaw adapter plugin design

## Goal

Expose a thin set of tools to OpenClaw agents and forward every call to the Python services.

OpenClaw should not own business logic, canonical storage, or retrieval policy.
It should only provide:
- agent tools
- optional HTTP routes for diagnostics
- optional background service for health checks

## Tools to expose

### Artifact tools
- artifact_create_task
- artifact_get
- artifact_put
- artifact_list
- artifact_update_state
- artifact_finalize_experience

### Thin KB tools
- kb_search
- kb_get
- kb_related

### Memory tools
Do not reimplement these.
Use @mem0/openclaw-mem0 directly for:
- memory_search
- memory_store
- memory_get
- memory_list
- memory_forget

## Plugin layout

openclaw/
  plugin_adapter/
    package.json
    tsconfig.json
    src/
      index.ts
      api_client.ts
      tools/
        artifact.ts
        kb.ts

## Design constraints

- Plugin code must stay stateless.
- Business validation happens in Python services.
- Tool schemas should be narrow and explicit.
- Errors should be normalized to stable codes.
- Timeouts should be short and configurable.
