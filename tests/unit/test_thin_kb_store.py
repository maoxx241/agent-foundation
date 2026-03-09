from __future__ import annotations

from libs.storage.thin_kb_store import ThinKBStore


def test_upsert_search_and_related(tmp_path):
    store = ThinKBStore(tmp_path / "kb", tmp_path / "kb" / "manifest.sqlite3")
    store.upsert(
        {
            "id": "proc-1",
            "object_type": "procedure",
            "title": "Rebuild index",
            "summary": "Rebuild the local FTS index",
            "goal": "Restore search",
            "steps": ["Run the rebuild command"],
            "expected_outcomes": ["Search returns fresh results"],
        }
    )
    store.upsert(
        {
            "id": "claim-1",
            "object_type": "claim",
            "title": "SQLite FTS is sufficient",
            "summary": "Phase 1 uses SQLite FTS5 for search",
            "subject": "Phase 1",
            "predicate": "uses",
            "statement": "Phase 1 uses SQLite FTS5 for simple search",
            "related_ids": ["proc-1"],
            "domain_tags": ["sqlite", "fts"],
        }
    )

    response = store.search(query="SQLite", object_types=["claim"], limit=10)
    assert len(response.hits) == 1
    assert response.hits[0].id == "claim-1"
    assert response.hits[0].object_type == "claim"

    related = store.related("claim-1")
    assert related["related"][0]["id"] == "proc-1"

