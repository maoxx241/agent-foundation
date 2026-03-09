from __future__ import annotations

import importlib.util

import pytest

from libs.storage.fs_utils import ValidationError
from libs.storage.phase2_store import Phase2Store
from libs.storage.thin_kb_store import ThinKBStore

HAS_DOCLING = importlib.util.find_spec("docling") is not None
HAS_LANCEDB = importlib.util.find_spec("lancedb") is not None


def make_phase2_store(tmp_path) -> Phase2Store:
    kb_root = tmp_path / "kb"
    store = ThinKBStore(kb_root, kb_root / "manifest.sqlite3")
    return Phase2Store(kb_root=kb_root, db_path=store.db_path, tasks_root=tmp_path / "tasks", canonical_store=store)


@pytest.mark.skipif(not HAS_DOCLING, reason="docling is not installed")
def test_d04_docling_parse_is_deterministic_for_same_file(tmp_path):
    phase2 = make_phase2_store(tmp_path)
    source = tmp_path / "guide.md"
    source.write_text("# Guide\n\nHybrid retrieval keeps exact lookup stable.\n", encoding="utf-8")

    first = phase2.ingest_document({"path": str(source), "domain_tags": ["docs"]})
    second = phase2.ingest_document({"path": str(source), "domain_tags": ["docs"]})

    assert first.source_id == second.source_id
    assert [chunk.title for chunk in first.chunks] == [chunk.title for chunk in second.chunks]
    assert [chunk.content for chunk in first.chunks] == [chunk.content for chunk in second.chunks]


@pytest.mark.skipif(not HAS_DOCLING, reason="docling is not installed")
def test_d06_docling_preserves_code_block_content(tmp_path):
    phase2 = make_phase2_store(tmp_path)
    source = tmp_path / "code-heavy.md"
    source.write_text(
        "# Example\n\n```python\nprint('hello')\n```\n\nThe code block should stay visible.\n",
        encoding="utf-8",
    )

    bundle = phase2.ingest_document({"path": str(source)})
    rendered = "\n".join(chunk.content for chunk in bundle.chunks)
    assert "print('hello')" in rendered or 'print("hello")' in rendered


def test_t02_python_symbol_extraction_finds_functions_and_classes(tmp_path):
    phase2 = make_phase2_store(tmp_path)
    bundle = phase2.ingest_code(
        {
            "title": "symbols.py",
            "language": "python",
            "content": (
                "@decorator\n"
                "def choose_version(value: str) -> str:\n"
                "    match value:\n"
                "        case 'v1':\n"
                "            return 'stable'\n"
                "        case _:\n"
                "            return 'unknown'\n\n"
                "class RetrievalPlan:\n"
                "    pass\n"
            ),
        }
    )

    assert {chunk.title for chunk in bundle.chunks} >= {"choose_version", "RetrievalPlan"}
    assert {chunk.chunk_type for chunk in bundle.chunks} >= {"function", "class"}


def test_l06_empty_query_hybrid_search_abstains_with_error(tmp_path):
    phase2 = make_phase2_store(tmp_path)
    with pytest.raises(ValidationError) as exc_info:
        phase2.search_hybrid({"query": ""})
    assert "non-empty query" in str(exc_info.value)


def test_l09_domain_mismatch_returns_no_hits(tmp_path):
    phase2 = make_phase2_store(tmp_path)
    phase2.ingest_document({"title": "ops.md", "content": "Rollback the search index safely.", "domain_tags": ["ops"]})
    result = phase2.search_hybrid({"query": "rollback search", "domain_tags": ["api"], "limit": 10})
    assert result.hits == []


@pytest.mark.skipif(not HAS_LANCEDB, reason="lancedb is not installed")
def test_l03_lancedb_sync_creates_local_index_artifacts(tmp_path):
    phase2 = make_phase2_store(tmp_path)
    phase2.ingest_document({"title": "lance.md", "content": "Vector and hybrid retrieval metadata."})
    assert any(phase2.lancedb_root.iterdir())
