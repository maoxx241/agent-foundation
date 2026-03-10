from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from apps.artifact_api.main import create_app as create_artifact_app
from apps.thin_kb_api.main import create_app as create_kb_app
from packages.core.storage.artifact_store import ArtifactStore
from packages.core.storage.phase2_store import Phase2Store
from packages.core.storage.thin_kb_store import ThinKBStore
from tests.helpers import AGENT_HEADERS


def make_artifact_client(tmp_path) -> TestClient:
    return TestClient(create_artifact_app(ArtifactStore(tmp_path / "tasks")), headers=AGENT_HEADERS)


def make_kb_client(tmp_path) -> TestClient:
    kb_root = tmp_path / "kb"
    store = ThinKBStore(kb_root, kb_root / "manifest.sqlite3")
    store.upsert(
        {
            "id": "claim-1",
            "object_type": "claim",
            "title": "SQLite FTS baseline",
            "summary": "Exact retrieval still matters",
            "subject": "retrieval",
            "predicate": "uses",
            "statement": "Retrieval uses SQLite FTS as the exact baseline",
            "related_ids": ["decision-1"],
            "domain_tags": ["retrieval"],
            "version": "1.0.0",
        }
    )
    store.upsert(
        {
            "id": "procedure-1",
            "object_type": "procedure",
            "title": "Rebuild search index",
            "summary": "Restore manifest and rebuild search index",
            "goal": "Recover retrieval",
            "steps": ["restore manifest", "rebuild search index"],
            "expected_outcomes": ["search returns expected results"],
            "domain_tags": ["ops"],
        }
    )
    store.upsert(
        {
            "id": "case-1",
            "object_type": "case",
            "title": "Index drift",
            "summary": "Interrupted promotion can drift the index",
            "case_type": "failure_analysis",
            "symptom": "results missing after publish",
            "env": {"repo": "agent-foundation"},
            "domain_tags": ["ops"],
        }
    )
    store.upsert(
        {
            "id": "decision-1",
            "object_type": "decision",
            "title": "Keep exact retrieval",
            "summary": "Hybrid is a complement, not a replacement",
            "context": "Need stable version-aware lookup",
            "decision": "Keep exact retrieval as the baseline",
            "domain_tags": ["retrieval"],
        }
    )
    phase2 = Phase2Store(kb_root=kb_root, db_path=store.db_path, tasks_root=tmp_path / "tasks", canonical_store=store)
    return TestClient(create_kb_app(store, phase2), headers=AGENT_HEADERS)


def test_artifact_public_endpoints_roundtrip_contract(tmp_path):
    client = make_artifact_client(tmp_path)
    task_id = "contract-task"

    response = client.post(
        "/v1/tasks",
        json={"task_id": task_id, "project_id": "proj", "title": "Contract", "goal": "exercise endpoints"},
    )
    assert response.status_code == 200, response.text

    response = client.get(f"/v1/tasks/{task_id}")
    assert response.status_code == 200, response.text

    response = client.get(f"/v1/tasks/{task_id}/artifacts")
    assert response.status_code == 200, response.text

    response = client.put(
        f"/v1/tasks/{task_id}/artifacts/10_evidence/evidence-pack.json",
        json={"format": "json", "content": {"summary": "evidence"}},
    )
    assert response.status_code == 200, response.text

    response = client.get(f"/v1/tasks/{task_id}/artifacts/10_evidence/evidence-pack.json")
    assert response.status_code == 200, response.text

    response = client.patch(
        f"/v1/tasks/{task_id}/state",
        json={"target_state": "EVIDENCE_READY", "changed_by": "lead"},
    )
    assert response.status_code == 200, response.text

    response = client.get(f"/v1/tasks/{task_id}/bundle")
    assert response.status_code == 200, response.text

    response = client.post(f"/v1/tasks/{task_id}/experience/finalize")
    assert response.status_code == 409, response.text


def test_artifact_public_endpoints_negative_contract(tmp_path):
    client = make_artifact_client(tmp_path)

    response = client.post("/v1/tasks", json={"task_id": "missing-fields"})
    assert response.status_code == 422

    response = client.post(
        "/v1/tasks",
        json={"task_id": "dup-task", "project_id": "proj", "title": "dup", "goal": "dup"},
    )
    assert response.status_code == 200, response.text
    response = client.post(
        "/v1/tasks",
        json={"task_id": "dup-task", "project_id": "proj", "title": "dup", "goal": "dup"},
    )
    assert response.status_code == 409

    response = client.get("/v1/tasks/missing-task")
    assert response.status_code == 404

    response = client.put(
        "/v1/tasks/dup-task/artifacts/10_evidence/not-allowed.json",
        json={"format": "json", "content": {}},
    )
    assert response.status_code == 422

    response = client.patch("/v1/tasks/dup-task/state", json={"target_state": "NOT_A_STATE", "changed_by": "qa"})
    assert response.status_code == 422


def test_thin_kb_public_endpoints_roundtrip_contract(tmp_path):
    client = make_kb_client(tmp_path)
    now = datetime.now(timezone.utc).isoformat()

    assert client.post("/v1/kb/search", json={"query": "baseline"}).status_code == 200
    assert client.post("/v1/kb/claims/search", json={"query": "SQLite"}).status_code == 200
    assert client.post("/v1/kb/procedures/search", json={"query": "rebuild"}).status_code == 200
    assert client.post("/v1/kb/cases/search", json={"query": "drift"}).status_code == 200
    assert client.post("/v1/kb/decisions/search", json={"query": "exact"}).status_code == 200
    assert client.get("/v1/kb/object/claim-1").status_code == 200
    assert client.get("/v1/kb/related/claim-1").status_code == 200

    response = client.post(
        "/v1/kb/ingest/document",
        json={"title": "doc.md", "content": "# Retrieval\n\nHybrid retrieval augments exact lookup."},
    )
    assert response.status_code == 200, response.text

    response = client.post(
        "/v1/kb/ingest/code",
        json={"title": "code.py", "language": "python", "content": "def retrieve():\n    return 'hybrid retrieval'\n"},
    )
    assert response.status_code == 200, response.text

    response = client.post("/v1/kb/search/hybrid", json={"query": "hybrid retrieval"})
    assert response.status_code == 200, response.text

    response = client.post(
        "/v1/kb/writeback/refine",
        json={
            "persist": False,
            "experience_packet": {
                "task_id": "task-inline",
                "project_id": "proj",
                "summary": "Inline refinement",
                "validation_summary": "validated",
                "candidate_claims": ["Exact lookup remains mandatory"],
                "created_at": now,
                "updated_at": now,
            },
        },
    )
    assert response.status_code == 200, response.text


def test_thin_kb_public_endpoints_negative_contract(tmp_path):
    client = make_kb_client(tmp_path)

    assert client.post("/v1/kb/search", json={"query": [], "limit": -1}).status_code == 422
    assert client.get("/v1/kb/object/missing").status_code == 404
    assert client.get("/v1/kb/related/missing").status_code == 404
    assert client.post("/v1/kb/search/hybrid", json={"limit": 0}).status_code == 422
    assert client.post("/v1/kb/ingest/document", json={"title": "empty"}).status_code == 400
    assert client.post("/v1/kb/ingest/code", json={"title": "empty"}).status_code == 400
    assert client.post("/v1/kb/writeback/refine", json={}).status_code == 400
