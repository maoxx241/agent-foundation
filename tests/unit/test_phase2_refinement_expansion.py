from __future__ import annotations

import pytest

from packages.core.storage.fs_utils import NotFoundError
from packages.core.storage.phase2_store import Phase2Store
from packages.core.storage.thin_kb_store import ThinKBStore


def make_store(tmp_path) -> tuple[Phase2Store, ThinKBStore]:
    kb_root = tmp_path / "kb"
    canonical = ThinKBStore(kb_root, kb_root / "manifest.sqlite3")
    phase2 = Phase2Store(kb_root=kb_root, db_path=canonical.db_path, tasks_root=tmp_path / "tasks", canonical_store=canonical)
    return phase2, canonical


def test_refine_inline_packet_without_persist_keeps_canonical_store_clean(tmp_path):
    phase2, canonical = make_store(tmp_path)
    refined = phase2.refine_writeback(
        {
            "persist": False,
            "experience_packet": {
                "task_id": "task-inline",
                "project_id": "proj",
                "summary": "inline refinement",
                "validation_summary": "validated",
                "candidate_claims": ["Exact retrieval remains mandatory"],
                "candidate_procedures": ["Stop writes -> rebuild index -> verify search"],
                "candidate_cases": ["Index rebuild after failed publish"],
                "candidate_decisions": ["Use hybrid retrieval as a complement"],
                "created_at": "2026-03-09T00:00:00+00:00",
                "updated_at": "2026-03-09T00:00:00+00:00",
            },
        }
    )
    assert len(refined.object_ids) == 4
    assert canonical.search(query="mandatory", object_types=["claim"], limit=10).hits == []


def test_refine_procedure_text_expands_into_multiple_steps(tmp_path):
    phase2, _ = make_store(tmp_path)
    refined = phase2.refine_writeback(
        {
            "persist": False,
            "experience_packet": {
                "task_id": "task-steps",
                "project_id": "proj",
                "summary": "step parsing",
                "validation_summary": "validated",
                "candidate_procedures": ["Freeze writes -> restore manifest -> rebuild index"],
                "created_at": "2026-03-09T00:00:00+00:00",
                "updated_at": "2026-03-09T00:00:00+00:00",
            },
        }
    )
    procedure = refined.objects[0]
    assert procedure["object_type"] == "procedure"
    assert len(procedure["steps"]) == 3


def test_refine_task_id_missing_packet_raises_not_found(tmp_path):
    phase2, _ = make_store(tmp_path)
    with pytest.raises(NotFoundError):
        phase2.refine_writeback({"task_id": "missing-task", "persist": False})


def test_ingest_code_from_file_path_reads_source_text(tmp_path):
    phase2, _ = make_store(tmp_path)
    source = tmp_path / "module.py"
    source.write_text("def ping():\n    return 'pong'\n", encoding="utf-8")

    bundle = phase2.ingest_code({"path": str(source), "language": "python"})
    assert bundle.title == "module.py"
    assert any(chunk.title == "ping" for chunk in bundle.chunks)


def test_hybrid_search_combines_canonical_and_extract_hits(tmp_path):
    phase2, canonical = make_store(tmp_path)
    canonical.upsert(
        {
            "id": "claim-hybrid",
            "object_type": "claim",
            "title": "Hybrid baseline",
            "summary": "canonical result",
            "subject": "hybrid",
            "predicate": "uses",
            "statement": "Hybrid search uses canonical results",
        }
    )
    phase2.ingest_document({"title": "hybrid.md", "content": "Hybrid search also uses extracted chunks."})

    result = phase2.search_hybrid({"query": "hybrid search", "limit": 10})
    assert {hit.hit_type for hit in result.hits} >= {"canonical", "extract"}


def test_inline_document_ingest_is_deterministic_for_same_content(tmp_path):
    phase2, _ = make_store(tmp_path)
    first = phase2.ingest_document({"title": "inline.md", "content": "Deterministic inline content."})
    second = phase2.ingest_document({"title": "inline.md", "content": "Deterministic inline content."})

    assert first.source_id == second.source_id
    assert [chunk.content for chunk in first.chunks] == [chunk.content for chunk in second.chunks]
