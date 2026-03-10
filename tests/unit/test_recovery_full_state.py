from __future__ import annotations

import tarfile

from packages.core.storage.artifact_store import ArtifactStore
from packages.core.storage.fs_utils import ensure_dir
from packages.core.storage.recovery import backup_workspace, restore_workspace
from packages.core.storage.thin_kb_store import ThinKBStore
from packages.core.stores.ledger_store import LedgerStore


def test_backup_and_restore_full_state_root_roundtrip(tmp_path):
    tasks_root = tmp_path / "tasks"
    kb_root = tmp_path / "kb"
    indexes_root = tmp_path / "indexes"
    ledgers_root = tmp_path / "ledgers"
    replay_root = tmp_path / "replay"
    backups_root = tmp_path / "backups"
    observability_root = tmp_path / "observability"

    ArtifactStore(tasks_root).create_task(
        {"task_id": "task-state", "project_id": "proj", "title": "state", "goal": "full snapshot"}
    )
    kb_store = ThinKBStore(kb_root, indexes_root / "sqlite" / "manifest.sqlite3")
    kb_store.upsert(
        {
            "id": "claim-state",
            "object_type": "claim",
            "title": "State root backup",
            "summary": "full state backup works",
            "subject": "backup",
            "predicate": "captures",
            "statement": "Backup captures full state",
        }
    )
    LedgerStore(ledgers_root).append_task_event("task-state", "task_created", actor="test")
    ensure_dir(replay_root / "captured_runs" / "run-1")
    ensure_dir(backups_root)
    ensure_dir(observability_root)
    (replay_root / "captured_runs" / "run-1" / "marker.txt").write_text("captured", encoding="utf-8")
    (backups_root / "seed.txt").write_text("backup", encoding="utf-8")
    (observability_root / "events.jsonl").write_text('{"name":"seed"}\n', encoding="utf-8")

    archive = tmp_path / "state.tar.gz"
    result = backup_workspace(
        tasks_root=tasks_root,
        kb_root=kb_root,
        indexes_root=indexes_root,
        ledgers_root=ledgers_root,
        replay_root=replay_root,
        backups_root=backups_root,
        observability_root=observability_root,
        output_path=archive,
    )
    assert {"tasks", "kb", "indexes", "ledgers", "replay", "backups", "observability"}.issubset(set(result["sections"]))
    with tarfile.open(archive, "r:gz") as handle:
        names = handle.getnames()
    assert any(name.startswith("indexes/") for name in names)
    assert any(name.startswith("ledgers/") for name in names)
    assert any(name.startswith("replay/") for name in names)

    restored_root = tmp_path / "restored"
    restore = restore_workspace(
        archive_path=archive,
        tasks_root=restored_root / "tasks",
        kb_root=restored_root / "kb",
        indexes_root=restored_root / "indexes",
        ledgers_root=restored_root / "ledgers",
        replay_root=restored_root / "replay",
        backups_root=restored_root / "backups",
        observability_root=restored_root / "observability",
    )

    assert restore["reindexed_objects"] == 1
    assert (restored_root / "replay" / "captured_runs" / "run-1" / "marker.txt").read_text(encoding="utf-8") == "captured"
    assert ThinKBStore(restored_root / "kb", restored_root / "indexes" / "sqlite" / "manifest.sqlite3").search(
        query="State root backup",
        limit=10,
    ).hits
