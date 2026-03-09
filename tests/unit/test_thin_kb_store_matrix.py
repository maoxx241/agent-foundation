from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from libs.storage.fs_utils import NotFoundError
from libs.storage.thin_kb_store import ThinKBStore


def make_store(tmp_path):
    return ThinKBStore(tmp_path / "kb", tmp_path / "kb" / "manifest.sqlite3")


@pytest.mark.parametrize(
    ("payload", "expected_dir"),
    [
        (
            {
                "id": "claim-1",
                "object_type": "claim",
                "title": "Claim title",
                "summary": "summary",
                "subject": "phase2",
                "predicate": "uses",
                "statement": "Phase 2 uses hybrid retrieval",
            },
            "claims",
        ),
        (
            {
                "id": "procedure-1",
                "object_type": "procedure",
                "title": "Procedure title",
                "summary": "summary",
                "goal": "Restore retrieval",
                "steps": ["restore manifest", "rebuild index"],
                "expected_outcomes": ["search returns"],
            },
            "procedures",
        ),
        (
            {
                "id": "case-1",
                "object_type": "case",
                "title": "Case title",
                "summary": "summary",
                "case_type": "failure_analysis",
                "env": {"repo": "agent-foundation"},
            },
            "cases",
        ),
        (
            {
                "id": "decision-1",
                "object_type": "decision",
                "title": "Decision title",
                "summary": "summary",
                "context": "Need stable search",
                "decision": "Keep exact retrieval",
            },
            "decisions",
        ),
    ],
)
def test_k01_to_k04_valid_objects_persist(tmp_path, payload, expected_dir):
    store = make_store(tmp_path)
    record = store.upsert(payload)
    assert record["id"] == payload["id"]
    assert store.object_path(payload["object_type"], payload["id"]).parent.name == expected_dir
    assert store.get(payload["id"])["title"] == payload["title"]


def test_k06_deprecated_object_is_searchable_by_status(tmp_path):
    store = make_store(tmp_path)
    store.upsert(
        {
            "id": "claim-deprecated",
            "object_type": "claim",
            "title": "Legacy fact",
            "summary": "deprecated fact",
            "subject": "legacy",
            "predicate": "used",
            "statement": "Legacy fact",
            "status": "deprecated",
        }
    )
    response = store.search(query="legacy", object_types=["claim"], status="deprecated", limit=10)
    assert response.hits
    assert response.hits[0].status == "deprecated"


def test_k07_missing_object_raises_not_found(tmp_path):
    store = make_store(tmp_path)
    with pytest.raises(NotFoundError):
        store.get("missing-object")


def test_k09_tag_and_env_filters_return_correct_subset(tmp_path):
    store = make_store(tmp_path)
    store.upsert(
        {
            "id": "case-ops",
            "object_type": "case",
            "title": "Ops case",
            "summary": "ops only",
            "case_type": "incident",
            "env": {"repo": "agent-foundation", "branch": "main"},
            "domain_tags": ["ops"],
        }
    )
    store.upsert(
        {
            "id": "case-api",
            "object_type": "case",
            "title": "API case",
            "summary": "api only",
            "case_type": "incident",
            "env": {"repo": "other", "branch": "dev"},
            "domain_tags": ["api"],
        }
    )
    response = store.search(
        query="case",
        object_types=["case"],
        domain_tags=["ops"],
        env_filters={"repo": "agent-foundation"},
        limit=10,
    )
    assert [hit.id for hit in response.hits] == ["case-ops"]


def test_k10_related_returns_only_linked_objects(tmp_path):
    store = make_store(tmp_path)
    store.upsert(
        {
            "id": "procedure-1",
            "object_type": "procedure",
            "title": "Rebuild",
            "summary": "rebuild index",
            "goal": "Recover search",
            "steps": ["rebuild"],
            "expected_outcomes": ["search returns"],
        }
    )
    store.upsert(
        {
            "id": "claim-1",
            "object_type": "claim",
            "title": "Exact search baseline",
            "summary": "exact search stays important",
            "subject": "search",
            "predicate": "uses",
            "statement": "Search uses exact lookup",
            "related_ids": ["procedure-1"],
        }
    )
    assert store.related("claim-1")["related"] == [
        {
            "id": "procedure-1",
            "object_type": "procedure",
            "title": "Rebuild",
            "summary": "rebuild index",
            "status": "candidate",
        }
    ]


def test_k11_invalid_object_shape_is_rejected(tmp_path):
    store = make_store(tmp_path)
    with pytest.raises(PydanticValidationError):
        store.upsert(
            {
                "id": "procedure-bad",
                "object_type": "procedure",
                "title": "Broken procedure",
                "summary": "missing goal",
            }
        )


def test_k12_rebuild_index_restores_search_from_files(tmp_path):
    store = make_store(tmp_path)
    store.upsert(
        {
            "id": "claim-rebuild",
            "object_type": "claim",
            "title": "Rebuild manifest",
            "summary": "manifest can be rebuilt",
            "subject": "manifest",
            "predicate": "supports",
            "statement": "Manifest rebuild restores search",
        }
    )
    with store._connect() as conn:
        conn.execute("DELETE FROM kb_objects")
        conn.execute("DELETE FROM kb_objects_fts")
        conn.commit()

    assert store.search(query="rebuild", object_types=["claim"], limit=10).hits == []
    assert store.rebuild_index() == 1
    assert store.search(query="rebuild", object_types=["claim"], limit=10).hits[0].id == "claim-rebuild"
