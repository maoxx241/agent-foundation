# State Root Migration

## Goal

Move legacy repo-local runtime directories into the v7 state-root layout without changing public `v1` API paths.

## Steps

1. Export `AGENT_FOUNDATION_STATE_ROOT` to the target runtime location.
2. Run `python scripts/migrate_runtime_state.py`.
3. Verify the new layout contains:
   - `tasks/active`
   - `tasks/archived`
   - `kb/canonical`
   - `kb/candidates`
   - `kb/deprecated`
   - `indexes/sqlite`
   - `indexes/lancedb`
   - `ledgers/task_events`
   - `ledgers/kb_events`
   - `ledgers/audits`
4. Regenerate contracts if APIs changed:
   - `python scripts/generate_contract_artifacts.py`
5. Run the full regression suite:
   - `pytest -q`

## Notes

- The migration script refuses to overwrite non-empty destinations.
- Legacy `tasks/<task_id>` layouts are normalized into `tasks/active/<task_id>`.
- Legacy `kb/manifest.sqlite3` is moved into `indexes/sqlite/manifest.sqlite3`.
