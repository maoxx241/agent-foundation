from __future__ import annotations

from tests.helpers import make_kb_client


def test_k01_exact_trusted_lookup(tmp_path):
    client = make_kb_client(tmp_path)
    response = client.post(
        "/v1/kb/claims/search",
        json={"query": "claim-trusted", "status": "trusted"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["hits"][0]["id"] == "claim-trusted"
    assert payload["warnings"] == []


def test_k04_tag_filter_version_mismatch_filters_result(tmp_path):
    client = make_kb_client(tmp_path)
    response = client.post(
        "/v1/kb/procedures/search",
        json={"query": "", "domain_tags": ["ops"], "version": "9.9.9", "status": "candidate"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["hits"] == []


def test_k05_full_text_candidate_procedure_lookup(tmp_path):
    client = make_kb_client(tmp_path)
    response = client.post(
        "/v1/kb/procedures/search",
        json={"query": "snapshot", "status": "candidate"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["hits"][0]["id"] == "procedure-candidate"


def test_k08_exact_lookup_returns_warning_on_version_mismatch(tmp_path):
    client = make_kb_client(tmp_path)
    response = client.post(
        "/v1/kb/decisions/search",
        json={"query": "decision-versioned", "version": "0.0.1"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["hits"][0]["id"] == "decision-versioned"
    assert payload["warnings"]
    assert "Version mismatch" in payload["warnings"][0]

