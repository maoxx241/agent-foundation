from __future__ import annotations

from fastapi.testclient import TestClient

from apps.artifact_api.main import create_app as create_artifact_app
from apps.thin_kb_api.main import create_app as create_kb_app
from libs.observability import Observability, build_metrics_report, load_jsonl
from libs.storage.artifact_store import ArtifactStore
from libs.storage.phase2_store import Phase2Store
from libs.storage.thin_kb_store import ThinKBStore


def test_artifact_api_emits_trace_and_task_logs(tmp_path):
    observability = Observability(tmp_path / "observability" / "artifact_api")
    client = TestClient(create_artifact_app(ArtifactStore(tmp_path / "tasks"), observability))

    response = client.post(
        "/v1/tasks",
        headers={"x-trace-id": "trace-artifact-001"},
        json={"task_id": "task-observe", "project_id": "proj", "title": "obs", "goal": "trace"},
    )
    assert response.status_code == 200, response.text
    assert response.headers["x-trace-id"] == "trace-artifact-001"

    events = load_jsonl(observability.events_path)
    assert any(item["name"] == "task_created" and item["task_id"] == "task-observe" for item in events)
    assert any(item["trace_id"] == "trace-artifact-001" for item in events)

    report = build_metrics_report(observability.root)
    assert report["requests_total"] >= 1


def test_thin_kb_api_generates_trace_and_metrics(tmp_path):
    observability = Observability(tmp_path / "observability" / "thin_kb_api")
    kb_root = tmp_path / "kb"
    store = ThinKBStore(kb_root, kb_root / "manifest.sqlite3")
    store.upsert(
        {
            "id": "claim-observe",
            "object_type": "claim",
            "title": "Trace retrieval",
            "summary": "Search requests should emit metrics",
            "subject": "retrieval",
            "predicate": "emits",
            "statement": "Retrieval emits metrics",
        }
    )
    phase2 = Phase2Store(kb_root=kb_root, db_path=store.db_path, tasks_root=tmp_path / "tasks", canonical_store=store)
    client = TestClient(create_kb_app(store, phase2, observability))

    response = client.post("/v1/kb/search", json={"query": "metrics"})
    assert response.status_code == 200, response.text
    assert response.headers["x-trace-id"]

    response = client.post(
        "/v1/kb/writeback/refine",
        json={
            "persist": False,
            "experience_packet": {
                "task_id": "task-observe-kb",
                "project_id": "proj",
                "summary": "publish metrics",
                "validation_summary": "validated",
                "candidate_claims": ["Metrics hooks should stay visible"],
                "created_at": "2026-03-09T00:00:00+00:00",
                "updated_at": "2026-03-09T00:00:00+00:00",
            },
        },
    )
    assert response.status_code == 200, response.text

    events = load_jsonl(observability.events_path)
    assert any(item["name"] == "kb_publish" and item["task_id"] == "task-observe-kb" for item in events)

    report = build_metrics_report(observability.root)
    assert report["requests_total"] >= 2
