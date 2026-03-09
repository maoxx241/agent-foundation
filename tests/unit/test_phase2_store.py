from __future__ import annotations

from datetime import datetime, timezone

from libs.storage.phase2_store import Phase2Store
from libs.storage.thin_kb_store import ThinKBStore


def test_phase2_store_ingests_and_hybrid_searches(tmp_path):
    kb_root = tmp_path / "kb"
    store = ThinKBStore(kb_root, kb_root / "manifest.sqlite3")
    store.upsert(
        {
            "id": "claim-canonical",
            "object_type": "claim",
            "title": "Canonical hybrid claim",
            "summary": "Canonical objects stay searchable alongside extracts",
            "subject": "thin kb",
            "predicate": "supports",
            "statement": "Thin KB supports hybrid retrieval",
            "domain_tags": ["retrieval"],
        }
    )
    phase2 = Phase2Store(kb_root=kb_root, db_path=store.db_path, tasks_root=tmp_path / "tasks", canonical_store=store)

    document = phase2.ingest_document(
        {
            "title": "hybrid.md",
            "content": "# Hybrid Retrieval\n\nDocling-ready ingestion keeps extracted chunks reviewable.",
            "domain_tags": ["retrieval"],
        }
    )
    assert document.source_type == "document"
    assert document.chunks

    code = phase2.ingest_code(
        {
            "title": "pipeline.py",
            "language": "python",
            "content": "def rebuild_index():\n    return 'hybrid retrieval'\n\nclass RetrievalPipeline:\n    pass\n",
            "domain_tags": ["retrieval"],
        }
    )
    assert code.source_type == "code"
    assert {chunk.chunk_type for chunk in code.chunks} & {"function", "class"}

    hybrid = phase2.search_hybrid({"query": "hybrid retrieval", "domain_tags": ["retrieval"], "limit": 10})
    assert hybrid.hits
    assert any(hit.hit_type == "extract" for hit in hybrid.hits)
    assert any(hit.hit_type == "canonical" for hit in hybrid.hits)


def test_phase2_store_refines_and_persists_writeback(tmp_path):
    kb_root = tmp_path / "kb"
    store = ThinKBStore(kb_root, kb_root / "manifest.sqlite3")
    phase2 = Phase2Store(kb_root=kb_root, db_path=store.db_path, tasks_root=tmp_path / "tasks", canonical_store=store)
    now = datetime.now(timezone.utc).isoformat()

    refined = phase2.refine_writeback(
        {
            "persist": True,
            "experience_packet": {
                "task_id": "task-phase2",
                "project_id": "proj",
                "summary": "Refine reusable rollout knowledge",
                "validation_summary": "Validation passed in staging",
                "candidate_claims": ["Hybrid retrieval requires canonical search coverage"],
                "candidate_procedures": ["Freeze writes -> rebuild index -> verify search"],
                "candidate_decisions": ["Use extracted chunks to complement exact search"],
                "created_at": now,
                "updated_at": now,
            },
        }
    )

    assert refined.persisted is True
    assert len(refined.object_ids) == 3

    decision_search = store.search(query="complement exact search", object_types=["decision"], limit=10)
    assert decision_search.hits
    assert decision_search.hits[0].id in refined.object_ids
