from __future__ import annotations

import io
import json
import tarfile

import pytest

from packages.core.storage.artifact_store import ArtifactStore
from packages.core.storage.fs_utils import ValidationError
from packages.core.storage.recovery import backup_workspace, detect_manifest_mismatch, restore_workspace
from packages.core.storage.thin_kb_store import ThinKBStore


def test_r01_backup_archive_contains_manifest_and_sections(tmp_path):
    tasks_root = tmp_path / "tasks"
    kb_root = tmp_path / "kb"
    ArtifactStore(tasks_root).create_task(
        {"task_id": "task-backup", "project_id": "proj", "title": "backup", "goal": "archive"}
    )
    ThinKBStore(kb_root, kb_root / "manifest.sqlite3")

    archive = tmp_path / "backup.tar.gz"
    backup_workspace(tasks_root=tasks_root, kb_root=kb_root, output_path=archive)
    with tarfile.open(archive, "r:gz") as handle:
        names = handle.getnames()
    assert "manifest.json" in names
    assert any(name.startswith("tasks/") for name in names)
    assert any(name.startswith("kb/") for name in names)


def test_r02_detect_manifest_mismatch_reports_missing_in_manifest(tmp_path):
    kb_root = tmp_path / "kb"
    store = ThinKBStore(kb_root, kb_root / "manifest.sqlite3")
    raw_file = kb_root / "canonical" / "claims" / "orphan-claim.json"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text("{}", encoding="utf-8")

    mismatch = detect_manifest_mismatch(kb_root=kb_root, db_path=store.db_path)
    assert mismatch["missing_in_manifest"] == ["orphan-claim"]


def test_r03_restore_succeeds_without_observability_section(tmp_path):
    tasks_root = tmp_path / "tasks"
    kb_root = tmp_path / "kb"
    ArtifactStore(tasks_root).create_task(
        {"task_id": "task-restore-no-obs", "project_id": "proj", "title": "restore", "goal": "restore"}
    )
    kb_store = ThinKBStore(kb_root, kb_root / "manifest.sqlite3")
    kb_store.upsert(
        {
            "id": "claim-restore-no-obs",
            "object_type": "claim",
            "title": "Restore no obs",
            "summary": "restore works without observability",
            "subject": "restore",
            "predicate": "works",
            "statement": "Restore works without observability",
        }
    )
    archive = tmp_path / "backup-no-obs.tar.gz"
    backup_workspace(tasks_root=tasks_root, kb_root=kb_root, output_path=archive)

    result = restore_workspace(
        archive_path=archive,
        tasks_root=tmp_path / "restored" / "tasks",
        kb_root=tmp_path / "restored" / "kb",
    )
    assert result["reindexed_objects"] == 1


def test_r05_restore_rejects_unsafe_archive_member(tmp_path):
    archive = tmp_path / "unsafe.tar.gz"
    with tarfile.open(archive, "w:gz") as handle:
        manifest = json.dumps({"created_at": "now"}).encode("utf-8")
        info = tarfile.TarInfo("manifest.json")
        info.size = len(manifest)
        handle.addfile(info, io.BytesIO(manifest))

        escape = b"bad"
        info = tarfile.TarInfo("../escape.txt")
        info.size = len(escape)
        handle.addfile(info, io.BytesIO(escape))

    with pytest.raises(ValidationError, match="Unsafe archive member path"):
        restore_workspace(
            archive_path=archive,
            tasks_root=tmp_path / "restore" / "tasks",
            kb_root=tmp_path / "restore" / "kb",
        )
