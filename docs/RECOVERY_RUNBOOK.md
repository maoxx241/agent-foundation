# Recovery Runbook

## Backup

Create a backup archive for the local workspace:

```bash
.venv/bin/python scripts/backup_workspace.py --output backups/agent-foundation-$(date +%Y%m%d-%H%M%S).tar.gz
```

This captures:

- `tasks/`
- `kb/`
- `observability/` when present

Required backup content:

- `tasks/`
- `kb/canonical/`
- `kb/manifest.sqlite3`

If any required section is missing, backup creation fails explicitly.

## Restore

Restore into a clean target directory:

```bash
.venv/bin/python scripts/restore_workspace.py \
  --archive backups/agent-foundation-YYYYMMDD-HHMMSS.tar.gz \
  --tasks-root restored/tasks \
  --kb-root restored/kb \
  --observability-root restored/observability
```

Restore behavior:

- extracts the archive
- restores `tasks/`, `kb/`, and `observability/`
- rebuilds the Thin KB manifest/index from canonical JSON
- fails if manifest consistency is still broken after rebuild

## Consistency Check

Check manifest vs canonical files:

```bash
.venv/bin/python scripts/check_manifest_consistency.py --kb-root kb
```

## Restore Drill

1. Create a fresh backup archive.
2. Restore into a clean temporary directory.
3. Run the consistency check.
4. Run `pytest -q` or at least the recovery tests.
5. Confirm known tasks and KB objects are readable again.
