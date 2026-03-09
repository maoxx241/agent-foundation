# OPENCLAW_ADAPTER_SCOPE

## Adapter-only rule

The custom OpenClaw plugin is a transport and normalization layer.
It should not become the place where business logic lives.

## Responsibilities
- call Artifact API
- call Thin KB API
- normalize tool inputs/outputs
- optionally expose health checks

## Non-responsibilities
- memory backend
- artifact truth store
- KB truth store
- promotion/refinement logic
- workflow scheduling

## Tool contract shape

Every tool should return:
```json
{
  "ok": true,
  "message": "...",
  "data": { ... }
}
```

On failure:
```json
{
  "ok": false,
  "error_code": "...",
  "message": "..."
}
```
