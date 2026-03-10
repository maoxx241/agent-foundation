from __future__ import annotations

from tests.helpers import (
    create_task,
    make_artifact_client,
    patch_state,
    put_json,
    reach_impl_approved,
    reach_written_back,
)


def test_state_update_is_idempotent(tmp_path):
    client = make_artifact_client(tmp_path)
    task_id = "task-idempotent-state"
    create_task(client, task_id)
    put_json(client, task_id, "10_evidence", "evidence-pack.json", {"summary": "evidence"})

    response = patch_state(client, task_id, "EVIDENCE_READY", "lead")
    assert response.status_code == 200, response.text
    updated_at = response.json()["state"]["updated_at"]

    response = patch_state(client, task_id, "EVIDENCE_READY", "lead")
    assert response.status_code == 200, response.text
    assert response.json()["state"]["state"] == "EVIDENCE_READY"
    assert response.json()["state"]["updated_at"] == updated_at


def test_finalize_experience_is_idempotent(tmp_path):
    client = make_artifact_client(tmp_path)
    task_id = "task-idempotent-finalize"
    create_task(client, task_id)
    reach_written_back(client, task_id, full=True)

    response = client.post(f"/v1/tasks/{task_id}/experience/finalize")
    assert response.status_code == 200, response.text
    first = response.json()["finalization"]

    response = client.post(f"/v1/tasks/{task_id}/experience/finalize")
    assert response.status_code == 200, response.text
    second = response.json()["finalization"]

    assert response.json()["state"] == "WRITTEN_BACK"
    assert second == first


def test_written_back_can_roll_back_to_released_and_refinalize(tmp_path):
    client = make_artifact_client(tmp_path)
    task_id = "task-writeback-rollback"
    create_task(client, task_id)
    reach_written_back(client, task_id, full=True)

    response = patch_state(client, task_id, "RELEASED", "release")
    assert response.status_code == 200, response.text
    assert response.json()["state"]["state"] == "RELEASED"

    response = client.post(f"/v1/tasks/{task_id}/experience/finalize")
    assert response.status_code == 200, response.text
    assert response.json()["state"] == "WRITTEN_BACK"


def test_validation_failure_includes_rollback_hint(tmp_path):
    client = make_artifact_client(tmp_path)
    task_id = "task-validation-hint"
    create_task(client, task_id)
    reach_impl_approved(client, task_id, full=True)
    put_json(
        client,
        task_id,
        "60_validation",
        "validation-report.json",
        {
            "passed": False,
            "summary": "validation exposed testspec weakness",
            "root_cause_classification": "testspec_weakness",
        },
    )
    put_json(client, task_id, "60_validation", "regression.json", {"status": "failed"})

    response = patch_state(client, task_id, "VALIDATED", "qa")
    assert response.status_code == 409, response.text
    assert "TESTSPEC_FROZEN" in response.json()["detail"]


def test_rollback_requires_target_stage_artifacts(tmp_path):
    client = make_artifact_client(tmp_path)
    task_id = "task-rollback-gate"
    create_task(client, task_id)
    reach_written_back(client, task_id, full=True)

    changelog_path = tmp_path / "tasks" / "active" / task_id / "70_release" / "changelog.md"
    changelog_path.unlink()

    response = patch_state(client, task_id, "RELEASED", "release")
    assert response.status_code == 409, response.text
    assert "70_release/changelog.md" in response.json()["detail"]
