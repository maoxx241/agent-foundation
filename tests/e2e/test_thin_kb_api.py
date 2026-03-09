from __future__ import annotations

from fastapi.testclient import TestClient

from apps.thin_kb_api.main import create_app
from libs.storage.thin_kb_store import ThinKBStore


def make_client(tmp_path):
    store = ThinKBStore(tmp_path / "kb", tmp_path / "kb" / "manifest.sqlite3")
    store.upsert(
        {
            "id": "claim-1",
            "object_type": "claim",
            "title": "FTS claim",
            "summary": "Thin KB search uses SQLite FTS5",
            "subject": "Thin KB",
            "predicate": "uses",
            "statement": "Thin KB search uses SQLite FTS5",
            "related_ids": ["decision-1"],
        }
    )
    store.upsert(
        {
            "id": "decision-1",
            "object_type": "decision",
            "title": "Phase 1 search substrate",
            "summary": "Choose SQLite FTS5",
            "context": "Need a small, local search layer",
            "decision": "Use SQLite FTS5",
        }
    )
    app = create_app(store)
    return TestClient(app)


def test_thin_kb_api_search_get_and_related(tmp_path):
    client = make_client(tmp_path)

    response = client.post("/v1/kb/claims/search", json={"query": "SQLite"})
    assert response.status_code == 200
    assert response.json()["hits"][0]["id"] == "claim-1"

    response = client.get("/v1/kb/object/claim-1")
    assert response.status_code == 200
    assert response.json()["title"] == "FTS claim"

    response = client.get("/v1/kb/related/claim-1")
    assert response.status_code == 200
    assert response.json()["related"][0]["id"] == "decision-1"
