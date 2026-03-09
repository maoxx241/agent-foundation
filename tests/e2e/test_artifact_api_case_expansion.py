from __future__ import annotations

from tests.helpers import create_task, get_state, make_artifact_client, put_json, reach_written_back


def test_a02_duplicate_task_id_conflicts(tmp_path):
    client = make_artifact_client(tmp_path)
    create_task(client, "dup-task")

    response = client.post(
        "/v1/tasks",
        json={"task_id": "dup-task", "project_id": "proj", "title": "dup-task", "goal": "duplicate"},
    )
    assert response.status_code == 409


def test_a03_missing_task_returns_404(tmp_path):
    client = make_artifact_client(tmp_path)
    response = client.get("/v1/tasks/missing-task")
    assert response.status_code == 404


def test_a04_valid_artifact_write_is_retrievable(tmp_path):
    client = make_artifact_client(tmp_path)
    create_task(client, "task-roundtrip")

    put_json(client, "task-roundtrip", "10_evidence", "evidence-pack.json", {"summary": "evidence"})
    response = client.get("/v1/tasks/task-roundtrip/artifacts/10_evidence/evidence-pack.json")
    assert response.status_code == 200
    assert response.json()["content"]["summary"] == "evidence"


def test_a05_invalid_stage_is_rejected(tmp_path):
    client = make_artifact_client(tmp_path)
    create_task(client, "task-invalid-stage")

    response = client.put(
        "/v1/tasks/task-invalid-stage/artifacts/99_invalid/evidence-pack.json",
        json={"format": "json", "content": {"summary": "bad stage"}},
    )
    assert response.status_code == 422


def test_a07_artifact_list_groups_multiple_stages(tmp_path):
    client = make_artifact_client(tmp_path)
    create_task(client, "task-list")
    put_json(client, "task-list", "10_evidence", "evidence-pack.json", {"summary": "evidence"})
    put_json(client, "task-list", "20_design", "design-spec.json", {"objective": "design", "selected_option": "A"})

    response = client.get("/v1/tasks/task-list/artifacts")
    assert response.status_code == 200
    payload = response.json()["artifacts"]
    assert {item["name"] for item in payload["10_evidence"]} == {"evidence-pack.json"}
    assert {item["name"] for item in payload["20_design"]} == {"design-spec.json"}


def test_a12_same_put_twice_preserves_schema_identity(tmp_path):
    client = make_artifact_client(tmp_path)
    create_task(client, "task-idempotent-put")

    response = client.put(
        "/v1/tasks/task-idempotent-put/artifacts/10_evidence/evidence-pack.json",
        json={"format": "json", "content": {"summary": "first"}},
    )
    assert response.status_code == 200
    first = response.json()["content"]

    response = client.put(
        "/v1/tasks/task-idempotent-put/artifacts/10_evidence/evidence-pack.json",
        json={"format": "json", "content": {"summary": "second"}},
    )
    assert response.status_code == 200
    second = response.json()["content"]

    assert first["created_at"] == second["created_at"]
    assert second["summary"] == "second"


def test_a13_internal_only_artifacts_cannot_be_overwritten(tmp_path):
    client = make_artifact_client(tmp_path)
    create_task(client, "task-internal-only")

    response = client.put(
        "/v1/tasks/task-internal-only/artifacts/00_task/state.json",
        json={"format": "json", "content": {"state": "NEW"}},
    )
    assert response.status_code == 422


def test_a14_bundle_export_is_complete_after_written_back(tmp_path):
    client = make_artifact_client(tmp_path)
    create_task(client, "task-bundle")
    reach_written_back(client, "task-bundle", full=True)

    response = client.get("/v1/tasks/task-bundle/bundle")
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "WRITTEN_BACK"
    assert any(item["stage"] == "80_writeback" and item["name"] == "finalization.json" for item in payload["artifacts"])
    assert get_state(client, "task-bundle") == "WRITTEN_BACK"
