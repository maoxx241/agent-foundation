# Implementer

- Change runtime behavior only through `apps/`, `packages/core/services/`, `packages/core/workflow/`, and `packages/core/stores/`.
- Treat `contracts/*` as frozen outputs derived from runtime definitions. Regenerate them after API or schema changes.
- Keep repo-local runtime data out of the code tree. Use `AGENT_FOUNDATION_STATE_ROOT`.
- Any new schema-backed artifact or KB object field must have a backfill path in `packages/core/migrations/registry.py`.
