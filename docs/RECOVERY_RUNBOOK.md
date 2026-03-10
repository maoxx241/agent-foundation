# Recovery Runbook

## Backup

Create a backup archive for the configured state root:

```bash
python -m apps.cli.main backup-state --output /tmp/agent-foundation-$(date +%Y%m%d-%H%M%S).tar.gz
```

This captures:

- `${STATE_ROOT}/tasks`
- `${STATE_ROOT}/kb`
- `${STATE_ROOT}/indexes` when present
- `${STATE_ROOT}/ledgers` when present
- `${STATE_ROOT}/replay` when present
- `${STATE_ROOT}/backups` when present
- `${STATE_ROOT}/observability` when present

Required backup content:

- `tasks/`
- `kb/canonical/`
- `indexes/sqlite/manifest.sqlite3`

If any required section is missing, backup creation fails explicitly.

Optional backup sections:

- `indexes/`
- `ledgers/`
- `replay/`
- `backups/`
- `observability/`

## Restore

Restore into the configured state root:

```bash
python -m apps.cli.main restore-state --archive /tmp/agent-foundation-YYYYMMDD-HHMMSS.tar.gz
```

Restore behavior:

- extracts the archive
- restores `tasks/` and `kb/`
- restores `indexes/`, `ledgers/`, `replay/`, `backups/`, and `observability/` when those sections are present and corresponding roots are configured
- rebuilds the Thin KB manifest/index from canonical JSON
- fails if manifest consistency is still broken after rebuild

Compatibility note:

- New docs and new archives target `indexes/sqlite/manifest.sqlite3` as the canonical manifest DB location.
- Restore remains compatible with older archives that stored the manifest DB at `kb/manifest.sqlite3`.

## Consistency Check

Check manifest vs canonical files:

```bash
python scripts/check_manifest_consistency.py
```

## Restore Drill

1. Create a fresh backup archive.
2. Restore into a clean state root or isolated temporary environment.
3. Run the consistency check.
4. Run `pytest -q` or at least the recovery tests.
5. Confirm known tasks, KB objects, and any restored replay or ledger data are readable again.
