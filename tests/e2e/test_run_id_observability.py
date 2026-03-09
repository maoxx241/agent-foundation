from __future__ import annotations

from fastapi.testclient import TestClient

from apps.artifact_api.main import create_app as create_artifact_app
from libs.observability import Observability, load_jsonl
from libs.storage.artifact_store import ArtifactStore


def test_artifact_api_preserves_run_id_in_logs_and_headers(tmp_path):
    observability = Observability(tmp_path / "observability" / "artifact_api")
    client = TestClient(create_artifact_app(ArtifactStore(tmp_path / "tasks"), observability))

    response = client.post(
        "/v1/tasks",
        headers={"x-run-id": "shadow-run-001"},
        json={"task_id": "task-run-id", "project_id": "proj", "title": "run id", "goal": "trace run"},
    )
    assert response.status_code == 200, response.text
    assert response.headers["x-run-id"] == "shadow-run-001"

    events = load_jsonl(observability.events_path)
    assert any(item["run_id"] == "shadow-run-001" for item in events)
