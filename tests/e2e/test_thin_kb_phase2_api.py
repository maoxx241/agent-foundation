from __future__ import annotations

from fastapi.testclient import TestClient

from apps.artifact_api.main import create_app as create_artifact_app
from apps.thin_kb_api.main import create_app as create_kb_app
from packages.core.storage.artifact_store import ArtifactStore
from packages.core.storage.phase2_store import Phase2Store
from packages.core.storage.thin_kb_store import ThinKBStore
from tests.helpers import AGENT_HEADERS, create_task, put_json


def make_clients(tmp_path) -> tuple[TestClient, TestClient]:
    tasks_root = tmp_path / "tasks"
    artifact_client = TestClient(create_artifact_app(ArtifactStore(tasks_root)), headers=AGENT_HEADERS)

    kb_root = tmp_path / "kb"
    kb_store = ThinKBStore(kb_root, kb_root / "manifest.sqlite3")
    phase2_store = Phase2Store(
        kb_root=kb_root,
        db_path=kb_store.db_path,
        tasks_root=tasks_root,
        canonical_store=kb_store,
    )
    kb_client = TestClient(create_kb_app(kb_store, phase2_store), headers=AGENT_HEADERS)
    return artifact_client, kb_client


def test_phase2_ingest_and_hybrid_search_api(tmp_path):
    _, kb_client = make_clients(tmp_path)

    response = kb_client.post(
        "/v1/kb/ingest/document",
        json={
            "title": "phase2.md",
            "content": "# Phase 2\n\nHybrid retrieval adds extracted chunks to the canonical search surface.",
            "domain_tags": ["phase2"],
        },
    )
    assert response.status_code == 200, response.text
    source_id = response.json()["source_id"]

    response = kb_client.post(
        "/v1/kb/ingest/code",
        json={
            "title": "phase2.py",
            "language": "python",
            "content": "def hydrate_chunks():\n    return 'canonical search surface'\n",
            "domain_tags": ["phase2"],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["source_type"] == "code"

    response = kb_client.post(
        "/v1/kb/search/hybrid",
        json={"query": "canonical search surface", "source_types": ["document", "code"], "limit": 10},
    )
    assert response.status_code == 200, response.text
    hits = response.json()["hits"]
    assert any(hit["hit_type"] == "extract" for hit in hits)
    assert any(hit.get("source_id") == source_id for hit in hits)


def test_phase2_refine_writeback_api(tmp_path):
    artifact_client, kb_client = make_clients(tmp_path)
    create_task(artifact_client, "phase2-task")
    put_json(
        artifact_client,
        "phase2-task",
        "80_writeback",
        "experience-packet.json",
        {
            "project_id": "proj",
            "summary": "Writeback refinement should produce reusable objects",
            "validation_summary": "Validated in production-like staging",
            "candidate_claims": ["SQLite FTS remains the exact lookup baseline"],
            "candidate_procedures": ["Stop writes -> restore manifest -> rebuild search index"],
            "candidate_cases": ["Index drift after interrupted promotion"],
            "candidate_decisions": ["Use hybrid retrieval only as a complement to exact search"],
        },
    )

    response = kb_client.post("/v1/kb/writeback/refine", json={"task_id": "phase2-task", "persist": True})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["persisted"] is True
    assert len(payload["object_ids"]) == 4

    response = kb_client.post("/v1/kb/search", json={"query": "exact lookup baseline", "object_types": ["claim"]})
    assert response.status_code == 200, response.text
    assert response.json()["hits"][0]["id"] in payload["object_ids"]
