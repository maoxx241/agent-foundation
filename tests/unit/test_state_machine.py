from __future__ import annotations

import pytest

from packages.core.schemas import TaskState
from packages.core.storage.artifact_store import ArtifactStore
from packages.core.storage.fs_utils import ConflictError


def _create_task(store: ArtifactStore) -> str:
    store.create_task(
        {
            "task_id": "task-001",
            "project_id": "proj-001",
            "title": "Implement phase 1",
            "goal": "Ship the artifact service",
        }
    )
    return "task-001"


def test_state_transition_requires_evidence(tmp_path):
    store = ArtifactStore(tmp_path / "tasks")
    task_id = _create_task(store)

    with pytest.raises(ConflictError, match="evidence-pack.json"):
        store.update_state(task_id, TaskState.EVIDENCE_READY, "tester")


def test_review_with_unresolved_conditions_is_blocked(tmp_path):
    store = ArtifactStore(tmp_path / "tasks")
    task_id = _create_task(store)
    store.put_artifact(
        task_id,
        "10_evidence",
        "evidence-pack.json",
        "json",
        {"summary": "existing evidence"},
    )
    store.update_state(task_id, TaskState.EVIDENCE_READY, "tester")
    store.put_artifact(
        task_id,
        "20_design",
        "design-spec.json",
        "json",
        {"objective": "do the thing", "selected_option": "A"},
    )
    store.put_artifact(
        task_id,
        "20_design",
        "design-review.json",
        "json",
        {"verdict": "approve_with_conditions", "required_changes": ["fix naming"]},
    )

    with pytest.raises(ConflictError, match="unresolved conditions"):
        store.update_state(task_id, TaskState.DESIGN_APPROVED, "reviewer")

