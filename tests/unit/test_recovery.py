from __future__ import annotations

import io
import json
import tarfile

import pytest

from libs.storage.artifact_store import ArtifactStore
from libs.storage.fs_utils import ValidationError
from libs.storage.recovery import backup_workspace, detect_manifest_mismatch, restore_workspace
from libs.storage.thin_kb_store import ThinKBStore


def test_backup_and_restore_workspace_roundtrip(tmp_path):
    tasks_root = tmp_path / "tasks"
    kb_root = tmp_path / "kb"
    observability_root = tmp_path / "observability"
    store = ArtifactStore(tasks_root)
    store.create_task(
        {
            "task_id": "task-restore",
            "project_id": "proj",
            "title": "restore",
            "goal": "backup restore",
        }
    )
    kb_store = ThinKBStore(kb_root, kb_root / "manifest.sqlite3")
    kb_store.upsert(
        {
            "id": "claim-restore",
            "object_type": "claim",
            "title": "Restore works",
            "summary": "Backups can be restored",
            "subject": "backup",
            "predicate": "supports",
            "statement": "Backup restore works",
        }
    )
    observability_root.mkdir(parents=True, exist_ok=True)
    (observability_root / "events.jsonl").write_text('{"name":"seed"}\n', encoding="utf-8")

    archive = tmp_path / "backup.tar.gz"
    result = backup_workspace(
        tasks_root=tasks_root,
        kb_root=kb_root,
        observability_root=observability_root,
        output_path=archive,
    )
    assert archive.exists()
    assert "tasks" in result["sections"]

    restored_tasks = tmp_path / "restored" / "tasks"
    restored_kb = tmp_path / "restored" / "kb"
    restored_obs = tmp_path / "restored" / "observability"
    restore = restore_workspace(
        archive_path=archive,
        tasks_root=restored_tasks,
        kb_root=restored_kb,
        observability_root=restored_obs,
    )
    assert restore["reindexed_objects"] == 1
    assert ArtifactStore(restored_tasks).get_task("task-restore")["state"]["state"] == "NEW"
    assert ThinKBStore(restored_kb, restored_kb / "manifest.sqlite3").search(query="Restore", limit=10).hits


def test_detect_manifest_mismatch_finds_missing_files(tmp_path):
    kb_root = tmp_path / "kb"
    store = ThinKBStore(kb_root, kb_root / "manifest.sqlite3")
    store.upsert(
        {
            "id": "claim-mismatch",
            "object_type": "claim",
            "title": "Mismatch",
            "summary": "detect missing disk file",
            "subject": "manifest",
            "predicate": "tracks",
            "statement": "Manifest tracks file",
        }
    )
    assert detect_manifest_mismatch(kb_root=kb_root, db_path=store.db_path) == {
        "missing_in_manifest": [],
        "missing_on_disk": [],
    }

    (kb_root / "canonical" / "claims" / "claim-mismatch.json").unlink()
    mismatch = detect_manifest_mismatch(kb_root=kb_root, db_path=store.db_path)
    assert mismatch["missing_on_disk"] == ["claim-mismatch"]


def test_backup_fails_when_required_content_missing(tmp_path):
    tasks_root = tmp_path / "tasks"
    kb_root = tmp_path / "kb"
    tasks_root.mkdir()
    (kb_root / "canonical").mkdir(parents=True)

    with pytest.raises(ValidationError, match="kb/manifest.sqlite3"):
        backup_workspace(tasks_root=tasks_root, kb_root=kb_root, output_path=tmp_path / "broken.tar.gz")


def test_restore_fails_on_partial_archive(tmp_path):
    archive = tmp_path / "partial.tar.gz"
    with tarfile.open(archive, "w:gz") as handle:
        manifest = json.dumps({"created_at": "now"}).encode("utf-8")
        info = tarfile.TarInfo("manifest.json")
        info.size = len(manifest)
        handle.addfile(info, io.BytesIO(manifest))

    with pytest.raises(ValidationError, match="tasks/ content"):
        restore_workspace(
            archive_path=archive,
            tasks_root=tmp_path / "restore" / "tasks",
            kb_root=tmp_path / "restore" / "kb",
        )
