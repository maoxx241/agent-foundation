from __future__ import annotations

import ast
import hashlib
import importlib.util
import math
import re
from pathlib import Path
from typing import Any, Iterable, Optional

from libs.schemas import (
    ExperiencePacket,
    ExtractBundle,
    ExtractedChunk,
    HybridSearchHit,
    HybridSearchResponse,
    RefinedWriteback,
    SourceRecord,
)
from libs.storage.fs_utils import NotFoundError, ValidationError, ensure_dir, read_json, read_text, utc_now, write_json_atomic
from .thin_kb_store import ThinKBStore

SOURCE_DIRS = {
    "document": "documents",
    "code": "code",
}


class Phase2Store:
    def __init__(
        self,
        kb_root: Path,
        db_path: Optional[Path],
        tasks_root: Path,
        canonical_store: Optional[ThinKBStore] = None,
    ):
        self.kb_root = kb_root
        self.db_path = db_path or kb_root / "manifest.sqlite3"
        self.tasks_root = tasks_root
        self.sources_root = kb_root / "sources"
        self.extracts_root = kb_root / "extracts"
        self.lancedb_root = kb_root / "lancedb"
        self.canonical_store = canonical_store or ThinKBStore(kb_root=kb_root, db_path=self.db_path)
        for dir_name in SOURCE_DIRS.values():
            ensure_dir(self.sources_root / dir_name)
            ensure_dir(self.extracts_root / dir_name)
        ensure_dir(self.lancedb_root)

    def ingest_document(self, payload: dict[str, Any]) -> ExtractBundle:
        raw_path = payload.get("path")
        content = str(payload.get("content") or "").strip()
        path = Path(raw_path).expanduser().resolve() if raw_path else None
        if not content and path is None:
            raise ValidationError("Document ingestion requires either 'content' or 'path'")

        warnings: list[str] = []
        parser = "plain-text"
        if not content and path is not None:
            parser, content, parser_warnings = self._load_document_content(path)
            warnings.extend(parser_warnings)

        content_type = str(payload.get("content_type") or _guess_content_type(path, default="text/plain"))
        title = _resolve_title(payload, path, fallback="inline-document")
        checksum = _checksum(content)
        source_id = _source_id("document", title, checksum)
        now = utc_now()
        source = SourceRecord(
            source_id=source_id,
            source_type="document",
            title=title,
            path=str(path) if path else None,
            content_type=content_type,
            parser=parser,
            checksum=checksum,
            content=content,
            metadata=_metadata(payload),
            created_at=now,
            updated_at=now,
        )
        chunks = _chunk_document(
            source_id=source_id,
            title=title,
            content=content,
            language=str(payload.get("language") or "") or None,
            tags=list(payload.get("domain_tags", [])),
        )
        bundle = ExtractBundle(
            source_id=source_id,
            source_type="document",
            title=title,
            parser=parser,
            language=str(payload.get("language") or "") or None,
            warnings=warnings,
            chunks=chunks,
            created_at=now,
            updated_at=now,
        )
        self._write_source(source)
        self._write_extract_bundle(bundle)
        self._sync_lancedb_index()
        return bundle

    def ingest_code(self, payload: dict[str, Any]) -> ExtractBundle:
        raw_path = payload.get("path")
        content = str(payload.get("content") or "").rstrip()
        path = Path(raw_path).expanduser().resolve() if raw_path else None
        if not content and path is None:
            raise ValidationError("Code ingestion requires either 'content' or 'path'")
        if not content and path is not None:
            if not path.exists():
                raise NotFoundError(f"Source file not found: {path}")
            content = read_text(path)

        language = str(payload.get("language") or _guess_language(path)).strip() or "text"
        title = _resolve_title(payload, path, fallback="inline-code")
        checksum = _checksum(content)
        source_id = _source_id("code", title, checksum)
        warnings: list[str] = []
        parser = "plain-text"
        chunks: list[ExtractedChunk] = []

        if language == "python":
            if _tree_sitter_available():
                try:
                    chunks = _extract_python_tree_sitter(source_id, content, list(payload.get("domain_tags", [])))
                    parser = "tree-sitter-python"
                except Exception as exc:  # pragma: no cover - exercised only when optional deps exist
                    warnings.append(f"tree-sitter-python fallback to ast: {exc}")
            if not chunks:
                chunks = _extract_python_ast(source_id, content, list(payload.get("domain_tags", [])))
                parser = "python-ast"

        if not chunks:
            chunks = _chunk_document(
                source_id=source_id,
                title=title,
                content=content,
                language=language,
                tags=list(payload.get("domain_tags", [])),
                chunk_type="snippet",
            )

        now = utc_now()
        source = SourceRecord(
            source_id=source_id,
            source_type="code",
            title=title,
            path=str(path) if path else None,
            content_type="text/plain",
            language=language,
            parser=parser,
            checksum=checksum,
            content=content,
            metadata=_metadata(payload),
            created_at=now,
            updated_at=now,
        )
        bundle = ExtractBundle(
            source_id=source_id,
            source_type="code",
            title=title,
            parser=parser,
            language=language,
            warnings=warnings,
            chunks=chunks,
            created_at=now,
            updated_at=now,
        )
        self._write_source(source)
        self._write_extract_bundle(bundle)
        self._sync_lancedb_index()
        return bundle

    def search_hybrid(self, payload: dict[str, Any]) -> HybridSearchResponse:
        query = str(payload.get("query", "")).strip()
        if not query:
            raise ValidationError("Hybrid search requires a non-empty query")

        limit = int(payload.get("limit", 10))
        object_types = list(payload.get("object_types", []))
        domain_tags = list(payload.get("domain_tags", []))
        source_types = set(payload.get("source_types", []))
        canonical = self.canonical_store.search(
            query=query,
            object_types=object_types,
            domain_tags=domain_tags,
            version=payload.get("version"),
            scope=payload.get("scope"),
            status=payload.get("status"),
            limit=limit,
            env_filters=payload.get("env_filters"),
        )

        hits: list[HybridSearchHit] = [
            HybridSearchHit(
                id=hit.id,
                hit_type="canonical",
                title=hit.title,
                score=_normalize_canonical_score(hit.score),
                summary=hit.summary,
                snippet=hit.summary,
                object_type=hit.object_type,
                tags=hit.tags,
                metadata={
                    "source_refs": hit.source_refs,
                    "status": hit.status,
                    "version": _canonical_version(hit.id, self.canonical_store),
                },
            )
            for hit in canonical.hits
        ]

        query_terms = _tokenize(query)
        for bundle_path in self._extract_bundle_paths():
            bundle = read_json(bundle_path)
            if source_types and bundle.get("source_type") not in source_types:
                continue
            for chunk in bundle.get("chunks", []):
                chunk_tags = list(chunk.get("tags", []))
                if domain_tags and not set(domain_tags).issubset(set(chunk_tags)):
                    continue
                score = _hybrid_score(query_terms, f"{chunk.get('title', '')}\n{chunk.get('content', '')}")
                if score <= 0:
                    continue
                hits.append(
                    HybridSearchHit(
                        id=chunk["chunk_id"],
                        hit_type="extract",
                        title=chunk["title"],
                        score=score,
                        summary=bundle["title"],
                        snippet=_snippet(query_terms, chunk["content"]),
                        source_id=bundle["source_id"],
                        tags=chunk_tags,
                        metadata={
                            "source_type": bundle["source_type"],
                            "language": bundle.get("language"),
                            "parser": bundle.get("parser"),
                            "start_line": chunk.get("start_line"),
                            "end_line": chunk.get("end_line"),
                        },
                    )
                )

        hits.sort(key=lambda item: item.score, reverse=True)
        return HybridSearchResponse(query=query, hits=hits[:limit], warnings=canonical.warnings)

    def refine_writeback(self, payload: dict[str, Any]) -> RefinedWriteback:
        packet = self._load_experience_packet(payload)
        persist = bool(payload.get("persist", False))
        objects: list[dict[str, Any]] = []
        warnings: list[str] = []

        for text in packet.candidate_claims:
            objects.append(_claim_from_text(packet, text))
        for text in packet.candidate_procedures:
            objects.append(_procedure_from_text(packet, text))
        for text in packet.candidate_cases:
            objects.append(_case_from_text(packet, text))
        for text in packet.candidate_decisions:
            objects.append(_decision_from_text(packet, text))

        if not objects:
            warnings.append("No candidate canonical objects were found in the ExperiencePacket")

        object_ids: list[str] = []
        if persist:
            for item in objects:
                persisted = self.canonical_store.upsert(item)
                object_ids.append(persisted["id"])
        else:
            object_ids = [item["id"] for item in objects]

        now = utc_now()
        summary = f"Refined {len(objects)} canonical object(s) from task {packet.task_id}"
        return RefinedWriteback(
            task_id=packet.task_id,
            persisted=persist,
            summary=summary,
            object_ids=object_ids,
            objects=objects,
            warnings=warnings,
            created_at=now,
            updated_at=now,
        )

    def _load_document_content(self, path: Path) -> tuple[str, str, list[str]]:
        if not path.exists():
            raise NotFoundError(f"Source file not found: {path}")
        warnings: list[str] = []
        if _docling_available():
            try:
                from docling.document_converter import DocumentConverter

                converter = DocumentConverter()
                result = converter.convert(str(path))
                document = getattr(result, "document", result)
                export = getattr(document, "export_to_markdown", None)
                if callable(export):
                    return "docling", str(export()), warnings
            except Exception as exc:  # pragma: no cover - exercised only when optional deps exist
                warnings.append(f"docling fallback to plain text: {exc}")
        return "plain-text", read_text(path), warnings

    def _load_experience_packet(self, payload: dict[str, Any]) -> ExperiencePacket:
        inline_packet = payload.get("experience_packet")
        if inline_packet:
            return ExperiencePacket.model_validate(inline_packet)

        task_id = str(payload.get("task_id") or "").strip()
        if not task_id:
            raise ValidationError("Writeback refinement requires either 'task_id' or 'experience_packet'")

        path = self.tasks_root / task_id / "80_writeback" / "experience-packet.json"
        if not path.exists():
            raise NotFoundError(f"Experience packet not found: {path}")
        return ExperiencePacket.model_validate(read_json(path))

    def _write_source(self, source: SourceRecord) -> None:
        path = self.sources_root / SOURCE_DIRS[source.source_type] / f"{source.source_id}.json"
        write_json_atomic(path, source.model_dump(mode="json"))

    def _write_extract_bundle(self, bundle: ExtractBundle) -> None:
        path = self.extracts_root / SOURCE_DIRS[bundle.source_type] / f"{bundle.source_id}.json"
        write_json_atomic(path, bundle.model_dump(mode="json"))

    def _extract_bundle_paths(self) -> Iterable[Path]:
        for dir_name in SOURCE_DIRS.values():
            yield from sorted((self.extracts_root / dir_name).glob("*.json"))

    def _sync_lancedb_index(self) -> None:
        if not _lancedb_available():
            return
        rows: list[dict[str, Any]] = []
        for path in self._extract_bundle_paths():
            bundle = read_json(path)
            for chunk in bundle.get("chunks", []):
                rows.append(
                    {
                        "id": chunk["chunk_id"],
                        "source_id": bundle["source_id"],
                        "source_type": bundle["source_type"],
                        "title": chunk["title"],
                        "content": chunk["content"],
                        "tags": ",".join(chunk.get("tags", [])),
                        "vector": _hash_vector(chunk["content"]),
                    }
                )
        try:
            import lancedb

            db = lancedb.connect(str(self.lancedb_root))
            db.create_table(
                "hybrid_chunks",
                data=rows
                or [
                    {
                        "id": "__empty__",
                        "source_id": "__empty__",
                        "source_type": "document",
                        "title": "empty",
                        "content": "",
                        "tags": "",
                        "vector": [0.0] * 12,
                    }
                ],
                mode="overwrite",
            )
        except Exception:  # pragma: no cover - exercised only when optional deps exist
            return


def _metadata(payload: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(payload.get("metadata", {}))
    if "domain_tags" in payload and payload["domain_tags"]:
        metadata.setdefault("domain_tags", list(payload["domain_tags"]))
    return metadata


def _guess_content_type(path: Optional[Path], *, default: str) -> str:
    if path is None:
        return default
    if path.suffix.lower() in {".md", ".markdown"}:
        return "text/markdown"
    if path.suffix.lower() in {".rst", ".txt"}:
        return "text/plain"
    return default


def _guess_language(path: Optional[Path]) -> str:
    if path is None:
        return "text"
    return {
        ".py": "python",
        ".ts": "typescript",
        ".js": "javascript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
    }.get(path.suffix.lower(), "text")


def _resolve_title(payload: dict[str, Any], path: Optional[Path], *, fallback: str) -> str:
    if payload.get("title"):
        return str(payload["title"])
    if path is not None:
        return path.name
    return fallback


def _checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _source_id(source_type: str, title: str, checksum: str) -> str:
    prefix = "doc" if source_type == "document" else "code"
    return f"{prefix}-{_slug(title)}-{checksum[:10]}"


def _chunk_document(
    *,
    source_id: str,
    title: str,
    content: str,
    language: Optional[str],
    tags: list[str],
    chunk_type: str = "paragraph",
) -> list[ExtractedChunk]:
    parts = [part.strip() for part in re.split(r"\n\s*\n+", content) if part.strip()]
    if not parts and content.strip():
        parts = [content.strip()]
    if not parts:
        parts = [title]
    chunks: list[ExtractedChunk] = []
    lines = content.splitlines() or [content]
    cursor = 0
    for index, part in enumerate(parts, start=1):
        start_line = _find_line_number(lines, part, cursor)
        if start_line is not None:
            cursor = start_line
        end_line = start_line + max(len(part.splitlines()) - 1, 0) if start_line is not None else None
        chunk_title = _line_title(part, fallback=f"{title} #{index}")
        chunks.append(
            ExtractedChunk(
                chunk_id=f"{source_id}-chunk-{index}",
                source_id=source_id,
                chunk_type=chunk_type,
                title=chunk_title,
                content=part,
                language=language,
                start_line=start_line,
                end_line=end_line,
                tags=tags,
            )
        )
    return chunks


def _extract_python_ast(source_id: str, content: str, tags: list[str]) -> list[ExtractedChunk]:
    tree = ast.parse(content)
    lines = content.splitlines()
    chunks: list[ExtractedChunk] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node_type = "function"
        elif isinstance(node, ast.ClassDef):
            node_type = "class"
        else:
            continue
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", start)
        text = "\n".join(lines[start - 1 : end]) if start is not None and end is not None else node.name
        chunks.append(
            ExtractedChunk(
                chunk_id=f"{source_id}-{node_type}-{node.name}",
                source_id=source_id,
                chunk_type=node_type,
                title=node.name,
                content=text,
                language="python",
                start_line=start,
                end_line=end,
                tags=tags,
                metadata={"signature": _signature_line(text)},
            )
        )
    if not chunks:
        chunks = _chunk_document(
            source_id=source_id,
            title="module",
            content=content,
            language="python",
            tags=tags,
            chunk_type="module",
        )
    return chunks


def _extract_python_tree_sitter(source_id: str, content: str, tags: list[str]) -> list[ExtractedChunk]:
    from tree_sitter import Language, Parser
    import tree_sitter_python

    language = Language(tree_sitter_python.language())
    try:
        parser = Parser(language)
    except TypeError:  # pragma: no cover - depends on optional parser version
        parser = Parser()
        parser.language = language
    content_bytes = content.encode("utf-8")
    tree = parser.parse(content_bytes)
    chunks: list[ExtractedChunk] = []

    def walk(node: Any) -> None:
        if node.type in {"function_definition", "class_definition"}:
            name_node = node.child_by_field_name("name")
            name = content_bytes[name_node.start_byte : name_node.end_byte].decode("utf-8") if name_node else node.type
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            text = content_bytes[node.start_byte : node.end_byte].decode("utf-8")
            chunk_type = "function" if node.type == "function_definition" else "class"
            chunks.append(
                ExtractedChunk(
                    chunk_id=f"{source_id}-{chunk_type}-{name}",
                    source_id=source_id,
                    chunk_type=chunk_type,
                    title=name,
                    content=text,
                    language="python",
                    start_line=start_line,
                    end_line=end_line,
                    tags=tags,
                    metadata={"signature": _signature_line(text)},
                )
            )
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return chunks


def _hybrid_score(query_terms: list[str], text: str) -> float:
    text_terms = _tokenize(text)
    if not query_terms or not text_terms:
        return 0.0
    keyword_hits = len(set(query_terms) & set(text_terms)) / len(set(query_terms))
    vector_score = _cosine_similarity(_hash_vector(" ".join(query_terms)), _hash_vector(text))
    return round((0.4 * keyword_hits) + (0.6 * vector_score), 6)


def _hash_vector(text: str, dimensions: int = 12) -> list[float]:
    vector = [0.0] * dimensions
    for token in _tokenize(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for index in range(dimensions):
            value = digest[index] / 255.0
            vector[index] += (value * 2.0) - 1.0
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 6) for value in vector]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    return max(sum(a * b for a, b in zip(left, right)), 0.0)


def _snippet(query_terms: list[str], content: str, window: int = 140) -> str:
    lowered = content.lower()
    position = min((lowered.find(term) for term in query_terms if term in lowered), default=-1)
    if position < 0:
        return content[:window]
    start = max(position - 30, 0)
    return content[start : start + window]


def _normalize_canonical_score(score: float) -> float:
    if score <= 0:
        return 0.75
    return round(1.0 / (1.0 + score), 6)


def _canonical_version(object_id: str, store: ThinKBStore) -> str | None:
    try:
        payload = store.get(object_id)
    except NotFoundError:
        return None
    return payload.get("version") or (payload.get("metadata") or {}).get("version")


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_][a-z0-9_/-]*", text.lower())


def _docling_available() -> bool:
    return importlib.util.find_spec("docling") is not None


def _tree_sitter_available() -> bool:
    return importlib.util.find_spec("tree_sitter") is not None and importlib.util.find_spec("tree_sitter_python") is not None


def _lancedb_available() -> bool:
    return importlib.util.find_spec("lancedb") is not None


def _find_line_number(lines: list[str], part: str, cursor: int) -> Optional[int]:
    anchor = part.splitlines()[0].strip()
    if not anchor:
        return None
    for index in range(max(cursor, 0), len(lines)):
        if anchor in lines[index]:
            return index + 1
    return None


def _line_title(text: str, *, fallback: str) -> str:
    first = text.splitlines()[0].strip().lstrip("#").strip()
    return first[:80] if first else fallback


def _signature_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:120]
    return ""


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "item"


def _statement_title(text: str) -> str:
    return text.strip().rstrip(".")[:80] or "candidate"


def _related_ref_ids(packet: ExperiencePacket) -> list[str]:
    return [ref.id for ref in packet.related_artifacts if ref.id]


def _domain_tags(packet: ExperiencePacket) -> list[str]:
    tags = packet.metadata.get("domain_tags", []) if isinstance(packet.metadata, dict) else []
    return [str(tag) for tag in tags]


def _version(packet: ExperiencePacket) -> Optional[str]:
    version = packet.metadata.get("version") if isinstance(packet.metadata, dict) else None
    return str(version) if version else None


def _claim_from_text(packet: ExperiencePacket, text: str) -> dict[str, Any]:
    statement = text.strip()
    subject, predicate, object_value = _split_claim(statement)
    return {
        "id": f"claim-{_slug(packet.task_id)}-{_slug(statement)[:32]}",
        "object_type": "claim",
        "title": _statement_title(statement),
        "summary": packet.summary,
        "version": _version(packet),
        "scope": "project",
        "status": "candidate",
        "domain_tags": _domain_tags(packet),
        "source_refs": _related_ref_ids(packet),
        "metadata": {"task_id": packet.task_id, "refined_from": "experience-packet"},
        "subject": subject,
        "predicate": predicate,
        "object_value": object_value,
        "statement": statement,
        "confidence": 0.7,
        "env": packet.env.model_dump(mode="json"),
    }


def _procedure_from_text(packet: ExperiencePacket, text: str) -> dict[str, Any]:
    steps = [part.strip() for part in re.split(r"(?:\s*->\s*|\n+|\d+\.\s*)", text) if part.strip()]
    if len(steps) <= 1:
        steps = [sentence.strip() for sentence in re.split(r"[.;]", text) if sentence.strip()]
    goal = steps[0] if steps else text.strip()
    return {
        "id": f"procedure-{_slug(packet.task_id)}-{_slug(goal)[:32]}",
        "object_type": "procedure",
        "title": _statement_title(goal),
        "summary": packet.fix_summary or packet.summary,
        "version": _version(packet),
        "scope": "project",
        "status": "candidate",
        "domain_tags": _domain_tags(packet),
        "source_refs": _related_ref_ids(packet),
        "metadata": {"task_id": packet.task_id, "refined_from": "experience-packet"},
        "goal": goal,
        "steps": steps or [text.strip()],
        "expected_outcomes": [packet.validation_summary],
        "failure_modes": [packet.root_cause] if packet.root_cause else [],
    }


def _case_from_text(packet: ExperiencePacket, text: str) -> dict[str, Any]:
    title = _statement_title(text)
    return {
        "id": f"case-{_slug(packet.task_id)}-{_slug(title)[:32]}",
        "object_type": "case",
        "title": title,
        "summary": packet.summary,
        "version": _version(packet),
        "scope": "project",
        "status": "candidate",
        "domain_tags": _domain_tags(packet),
        "source_refs": _related_ref_ids(packet),
        "metadata": {"task_id": packet.task_id, "refined_from": "experience-packet"},
        "case_type": "failure_analysis" if packet.root_cause else "experiment",
        "symptom": text.strip(),
        "root_cause": packet.root_cause,
        "resolution": packet.fix_summary,
        "env": packet.env.model_dump(mode="json"),
        "outcome": packet.validation_summary,
    }


def _decision_from_text(packet: ExperiencePacket, text: str) -> dict[str, Any]:
    decision = text.strip()
    return {
        "id": f"decision-{_slug(packet.task_id)}-{_slug(decision)[:32]}",
        "object_type": "decision",
        "title": _statement_title(decision),
        "summary": packet.summary,
        "version": _version(packet),
        "scope": "project",
        "status": "candidate",
        "domain_tags": _domain_tags(packet),
        "source_refs": _related_ref_ids(packet),
        "metadata": {"task_id": packet.task_id, "refined_from": "experience-packet"},
        "context": packet.summary,
        "decision": decision,
        "tradeoffs": [packet.root_cause] if packet.root_cause else [],
        "consequences": [packet.validation_summary],
    }


def _split_claim(statement: str) -> tuple[str, str, Optional[str]]:
    for separator in (" is ", " uses ", " requires ", " enables ", " blocks "):
        if separator in statement:
            subject, remainder = statement.split(separator, 1)
            return subject.strip() or "system", separator.strip(), remainder.strip() or None
    words = statement.split()
    if len(words) >= 2:
        return words[0], words[1], " ".join(words[2:]) or None
    return statement or "system", "states", None
