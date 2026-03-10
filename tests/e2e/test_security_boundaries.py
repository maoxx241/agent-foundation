from __future__ import annotations

from tests.helpers import create_task, make_artifact_client, make_kb_client, put_json


def test_s01_task_isolation_prevents_cross_task_artifact_reads(tmp_path):
    client = make_artifact_client(tmp_path)
    create_task(client, "task-a")
    create_task(client, "task-b")
    put_json(client, "task-a", "10_evidence", "evidence-pack.json", {"summary": "task-a only"})

    response = client.get("/v1/tasks/task-b/artifacts/10_evidence/evidence-pack.json")
    assert response.status_code == 404


def test_s03_artifact_api_rejects_unknown_fields(tmp_path):
    client = make_artifact_client(tmp_path)
    response = client.post(
        "/v1/tasks",
        json={
            "task_id": "task-unknown-field",
            "project_id": "proj",
            "title": "unknown",
            "goal": "unknown",
            "unexpected": "boom",
        },
    )
    assert response.status_code == 422


def test_s03_artifact_api_rejects_path_escape_task_ids(tmp_path):
    client = make_artifact_client(tmp_path)
    response = client.post(
        "/v1/tasks",
        json={
            "task_id": "../task-escape",
            "project_id": "proj",
            "title": "escape",
            "goal": "escape",
        },
    )
    assert response.status_code == 422
    assert not any((tmp_path / "tasks" / "active").iterdir())


def test_s03_thin_kb_api_rejects_unknown_fields(tmp_path):
    client = make_kb_client(tmp_path)
    response = client.post("/v1/kb/search", json={"query": "fts", "unexpected": "boom"})
    assert response.status_code == 422


def test_s04_internal_artifact_path_cannot_be_traversed_or_bypassed(tmp_path):
    client = make_artifact_client(tmp_path)
    create_task(client, "task-boundary")
    response = client.put(
        "/v1/tasks/task-boundary/artifacts/80_writeback/finalization.json",
        json={"format": "json", "content": {"forced": True}},
    )
    assert response.status_code == 422
