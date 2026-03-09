from __future__ import annotations

from fastapi.testclient import TestClient

from apps.thin_kb_api.main import create_app
from libs.storage.thin_kb_store import ThinKBStore
from tests.helpers import make_kb_client


def test_k08_search_with_object_type_filter_returns_only_claims(tmp_path):
    client = make_kb_client(tmp_path)
    response = client.post("/v1/kb/search", json={"query": "Phase 1", "object_types": ["claim"], "limit": 10})
    assert response.status_code == 200
    assert {hit["object_type"] for hit in response.json()["hits"]} == {"claim"}


def test_k09_status_filter_returns_only_trusted_objects(tmp_path):
    client = make_kb_client(tmp_path)
    response = client.post("/v1/kb/search", json={"query": "", "status": "trusted", "limit": 10})
    assert response.status_code == 200
    assert [hit["id"] for hit in response.json()["hits"]] == ["claim-trusted"]


def test_k09_status_filter_returns_only_candidate_objects(tmp_path):
    client = make_kb_client(tmp_path)
    response = client.post("/v1/kb/search", json={"query": "", "status": "candidate", "limit": 10})
    assert response.status_code == 200
    assert {hit["id"] for hit in response.json()["hits"]} == {"procedure-candidate", "decision-versioned"}


def test_k08_non_exact_version_mismatch_filters_fuzzy_result(tmp_path):
    client = make_kb_client(tmp_path)
    response = client.post(
        "/v1/kb/decisions/search",
        json={"query": "version-aware lookups", "version": "0.0.1"},
    )
    assert response.status_code == 200
    assert response.json()["hits"] == []
    assert response.json()["warnings"] == []


def test_k08_exact_title_lookup_keeps_result_and_warns_on_version_mismatch(tmp_path):
    client = make_kb_client(tmp_path)
    response = client.post(
        "/v1/kb/decisions/search",
        json={"query": "Use versioned search filters", "version": "0.0.1"},
    )
    assert response.status_code == 200
    assert response.json()["hits"][0]["id"] == "decision-versioned"
    assert "Version mismatch" in response.json()["warnings"][0]


def test_k09_case_env_filter_mismatch_suppresses_result(tmp_path):
    store = ThinKBStore(tmp_path / "kb", tmp_path / "kb" / "manifest.sqlite3")
    store.upsert(
        {
            "id": "case-env",
            "object_type": "case",
            "title": "Benchmark case",
            "summary": "case with env data",
            "case_type": "benchmark",
            "env": {"repo": "agent-foundation", "branch": "main"},
        }
    )
    client = TestClient(create_app(store))
    response = client.post(
        "/v1/kb/cases/search",
        json={"query": "benchmark", "env_filters": {"repo": "missing"}, "limit": 10},
    )
    assert response.status_code == 200
    assert response.json()["hits"] == []
