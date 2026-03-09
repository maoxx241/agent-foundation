from __future__ import annotations

from fastapi.testclient import TestClient

from apps.artifact_api.main import create_app
from libs.storage.artifact_store import ArtifactStore
from tests.helpers import (
    create_task,
    get_state,
    patch_state,
    put_json,
    put_text,
    reach_design_approved,
    reach_impl_approved,
    reach_validated,
    reach_written_back,
)


def test_w04_impl_review_approved_task_can_roll_back_to_implemented(tmp_path):
    client = TestClient(create_app(ArtifactStore(tmp_path / "tasks")))
    create_task(client, "task-impl-rollback")
    reach_impl_approved(client, "task-impl-rollback", full=True)

    response = patch_state(client, "task-impl-rollback", "IMPLEMENTED", "review")
    assert response.status_code == 200
    assert get_state(client, "task-impl-rollback") == "IMPLEMENTED"


def test_w05_validated_task_can_roll_back_to_implemented_for_bug_fix(tmp_path):
    client = TestClient(create_app(ArtifactStore(tmp_path / "tasks")))
    create_task(client, "task-validation-bug")
    reach_validated(client, "task-validation-bug", full=True)

    response = patch_state(client, "task-validation-bug", "IMPLEMENTED", "qa")
    assert response.status_code == 200
    assert get_state(client, "task-validation-bug") == "IMPLEMENTED"


def test_w06_validated_task_can_roll_back_to_testspec_for_spec_issue(tmp_path):
    client = TestClient(create_app(ArtifactStore(tmp_path / "tasks")))
    create_task(client, "task-validation-spec")
    reach_validated(client, "task-validation-spec", full=True)

    response = patch_state(client, "task-validation-spec", "TESTSPEC_FROZEN", "qa")
    assert response.status_code == 200
    assert get_state(client, "task-validation-spec") == "TESTSPEC_FROZEN"


def test_w09_restart_recovery_keeps_task_state_consistent(tmp_path):
    tasks_root = tmp_path / "tasks"
    client = TestClient(create_app(ArtifactStore(tasks_root)))
    create_task(client, "task-restart")
    reach_design_approved(client, "task-restart", full=True)
    put_json(client, "task-restart", "30_test", "test-spec.json", {"strategy_summary": "restart-safe"})
    put_json(client, "task-restart", "30_test", "acceptance.json", {"criteria": ["restart-safe"]})
    response = patch_state(client, "task-restart", "TESTSPEC_FROZEN", "qa")
    assert response.status_code == 200

    restarted = TestClient(create_app(ArtifactStore(tasks_root)))
    assert get_state(restarted, "task-restart") == "TESTSPEC_FROZEN"
    put_text(restarted, "task-restart", "40_dev", "patch.diff", "diff --git a/a.py b/a.py")
    put_json(restarted, "task-restart", "40_dev", "changed-files.json", ["a.py"])
    put_json(restarted, "task-restart", "40_dev", "selftest.json", {"passed": True, "summary": "restart green"})
    response = patch_state(restarted, "task-restart", "IMPLEMENTED", "engineer")
    assert response.status_code == 200


def test_w10_written_back_task_can_roll_back_to_released_and_forward_again(tmp_path):
    client = TestClient(create_app(ArtifactStore(tmp_path / "tasks")))
    create_task(client, "task-partial-rollback")
    reach_written_back(client, "task-partial-rollback", full=True)

    response = patch_state(client, "task-partial-rollback", "RELEASED", "release")
    assert response.status_code == 200
    assert get_state(client, "task-partial-rollback") == "RELEASED"

    put_json(
        client,
        "task-partial-rollback",
        "80_writeback",
        "experience-packet.json",
        {
            "project_id": "proj",
            "summary": "refreshed experience",
            "validation_summary": "all green",
            "candidate_claims": ["refresh writeback"],
        },
    )
    response = client.post("/v1/tasks/task-partial-rollback/experience/finalize")
    assert response.status_code == 200
    assert get_state(client, "task-partial-rollback") == "WRITTEN_BACK"
