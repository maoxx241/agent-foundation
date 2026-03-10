from __future__ import annotations

from fastapi.testclient import TestClient

from apps.artifact_api.main import create_app as create_artifact_app
from apps.thin_kb_api.main import create_app as create_kb_app
from packages.core.storage.artifact_store import ArtifactStore
from packages.core.storage.phase2_store import Phase2Store
from packages.core.storage.thin_kb_store import ThinKBStore
from tests.helpers import AGENT_HEADERS, OPERATOR_HEADERS


def test_public_endpoints_require_service_token(tmp_path):
    client = TestClient(create_artifact_app(ArtifactStore(tmp_path / "tasks")))
    response = client.post(
        "/v1/tasks",
        json={"task_id": "task-no-token", "project_id": "proj", "title": "token", "goal": "auth"},
    )
    assert response.status_code == 401


def test_agent_token_cannot_call_operator_endpoints(tmp_path):
    store = ArtifactStore(tmp_path / "tasks")
    client = TestClient(create_artifact_app(store), headers=AGENT_HEADERS)
    response = client.get("/internal/v1/audit/task/task-1")
    assert response.status_code == 403


def test_writeback_persist_creates_candidates_then_operator_promotes_and_deprecates(tmp_path):
    tasks_root = tmp_path / "tasks"
    artifact_client = TestClient(create_artifact_app(ArtifactStore(tasks_root)), headers=AGENT_HEADERS)

    kb_root = tmp_path / "kb"
    kb_store = ThinKBStore(kb_root, tmp_path / "indexes" / "sqlite" / "manifest.sqlite3")
    phase2_store = Phase2Store(
        kb_root=kb_root,
        db_path=kb_store.db_path,
        tasks_root=tasks_root,
        canonical_store=kb_store,
        lancedb_root=tmp_path / "indexes" / "lancedb",
    )
    kb_client = TestClient(create_kb_app(kb_store, phase2_store), headers=AGENT_HEADERS)
    operator_client = TestClient(create_kb_app(kb_store, phase2_store), headers=OPERATOR_HEADERS)

    response = artifact_client.post(
        "/v1/tasks",
        json={"task_id": "task-audit", "project_id": "proj", "title": "audit", "goal": "writeback"},
    )
    assert response.status_code == 200, response.text
    response = artifact_client.put(
        "/v1/tasks/task-audit/artifacts/80_writeback/experience-packet.json",
        json={
            "format": "json",
            "content": {
                "project_id": "proj",
                "summary": "candidate-only persist",
                "validation_summary": "validated",
                "candidate_claims": ["Exact lookup remains mandatory"],
            },
        },
    )
    assert response.status_code == 200, response.text

    response = kb_client.post("/v1/kb/writeback/refine", json={"task_id": "task-audit", "persist": True})
    assert response.status_code == 200, response.text
    payload = response.json()
    candidate_id = payload["object_ids"][0]
    assert payload["persist_target"] == "candidate"
    assert payload["object_status"] == "candidate"

    response = kb_client.get(f"/v1/kb/object/{candidate_id}")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "candidate"

    response = operator_client.post(
        f"/internal/v1/kb/candidates/{candidate_id}/promote",
        json={"changed_by": "operator", "reason": "reviewed"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "trusted"
    assert response.json()["promotion_source"]["source_candidate_id"] == candidate_id

    response = operator_client.post(
        f"/internal/v1/kb/object/{candidate_id}/deprecate",
        json={"changed_by": "operator", "reason": "replaced", "superseded_by": "claim-next"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "deprecated"
    assert response.json()["deprecated_reason"] == "replaced"

    audit = operator_client.get(f"/internal/v1/audit/object/{candidate_id}")
    assert audit.status_code == 200, audit.text
    event_types = [event["event_type"] for event in audit.json()["events"]]
    assert "candidate_created" in event_types
    assert "candidate_promoted" in event_types
    assert "object_deprecated" in event_types
    assert "object_superseded" in event_types


def test_operator_can_archive_task_and_read_audit_log(tmp_path):
    store = ArtifactStore(tmp_path / "tasks")
    agent_client = TestClient(create_artifact_app(store), headers=AGENT_HEADERS)
    operator_client = TestClient(create_artifact_app(store), headers=OPERATOR_HEADERS)

    response = agent_client.post(
        "/v1/tasks",
        json={"task_id": "task-archive", "project_id": "proj", "title": "archive", "goal": "ops"},
    )
    assert response.status_code == 200, response.text

    response = operator_client.post(
        "/internal/v1/tasks/task-archive/archive",
        json={"changed_by": "operator", "reason": "completed"},
    )
    assert response.status_code == 200, response.text

    response = agent_client.get("/v1/tasks/task-archive")
    assert response.status_code == 404

    audit = operator_client.get("/internal/v1/audit/task/task-archive")
    assert audit.status_code == 200, audit.text
    event_types = [event["event_type"] for event in audit.json()["events"]]
    assert "task_created" in event_types
    assert "task_archived" in event_types
