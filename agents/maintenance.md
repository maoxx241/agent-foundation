# Maintenance

- Use `scripts/migrate_runtime_state.py` to move legacy repo-local runtime data into `AGENT_FOUNDATION_STATE_ROOT`.
- Use `scripts/backup_workspace.py` and `scripts/restore_workspace.py` for backup and restore drills.
- Archive completed tasks through `/internal/v1/tasks/{task_id}/archive`.
- Promote or deprecate KB objects only through `/internal/v1/kb/*` operator endpoints.
