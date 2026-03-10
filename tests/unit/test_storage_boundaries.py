from __future__ import annotations

import pytest

from packages.core.storage.artifact_store import ArtifactStore
from packages.core.storage.fs_utils import ValidationError
from packages.core.storage.thin_kb_store import ThinKBStore


def test_create_task_rolls_back_on_store_validation_failure(tmp_path):
    store = ArtifactStore(tmp_path / "tasks")

    with pytest.raises(ValidationError):
        store.create_task(
            {
                "task_id": "task-invalid-priority",
                "project_id": "proj",
                "title": "broken",
                "goal": "exercise rollback",
                "priority": "urgent",
            }
        )

    assert not (tmp_path / "tasks" / "active" / "task-invalid-priority").exists()


def test_create_task_rejects_path_segment_escape(tmp_path):
    store = ArtifactStore(tmp_path / "tasks")

    with pytest.raises(ValidationError):
        store.create_task(
            {
                "task_id": "../escape",
                "project_id": "proj",
                "title": "escape",
                "goal": "should fail",
            }
        )

    assert list((tmp_path / "tasks" / "active").iterdir()) == []


def test_thin_kb_store_rejects_path_segment_escape_ids(tmp_path):
    store = ThinKBStore(tmp_path / "kb", tmp_path / "kb" / "manifest.sqlite3")

    with pytest.raises(ValidationError):
        store.upsert(
            {
                "id": "../claim-escape",
                "object_type": "claim",
                "title": "escape",
                "summary": "should fail",
                "subject": "phase2",
                "predicate": "uses",
                "statement": "should fail",
            }
        )
