from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Type, Union

from libs.schemas import Case, Claim, Decision, Procedure, SearchHit, SearchResponse
from libs.schemas.common import KBStatus, Scope
from libs.schemas.thin_kb import KBObject
from .fs_utils import NotFoundError, ValidationError, ensure_dir, read_json, utc_now, write_json_atomic

OBJECT_MODELS: dict[str, Type[KBObject]] = {
    "claim": Claim,
    "procedure": Procedure,
    "case": Case,
    "decision": Decision,
}

OBJECT_DIRS = {
    "claim": "claims",
    "procedure": "procedures",
    "case": "cases",
    "decision": "decisions",
}

MANIFEST_SQL = """
CREATE TABLE IF NOT EXISTS kb_objects (
  id TEXT PRIMARY KEY,
  object_type TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT,
  scope TEXT NOT NULL,
  status TEXT NOT NULL,
  trust_level TEXT NOT NULL,
  domain_tags_json TEXT NOT NULL,
  stack_tags_json TEXT NOT NULL,
  source_refs_json TEXT NOT NULL,
  related_ids_json TEXT NOT NULL,
  file_path TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS kb_objects_fts USING fts5(
  id UNINDEXED,
  object_type,
  title,
  summary,
  body_text,
  domain_tags,
  stack_tags
);
"""


class ThinKBStore:
    def __init__(self, kb_root: Path, db_path: Optional[Path] = None):
        self.kb_root = kb_root
        self.canonical_root = self.kb_root / "canonical"
        self.db_path = db_path or self.kb_root / "manifest.sqlite3"
        for dir_name in OBJECT_DIRS.values():
            ensure_dir(self.canonical_root / dir_name)
        self._init_db()

    def upsert(self, payload: dict[str, Any]) -> dict[str, Any]:
        object_type = str(payload.get("object_type", "")).strip()
        model_cls = OBJECT_MODELS.get(object_type)
        if model_cls is None:
            raise ValidationError(f"Unsupported KB object type: {object_type}")

        item = dict(payload)
        existing = self._find_existing(item["id"]) if item.get("id") else None
        if existing and "created_at" in existing:
            item.setdefault("created_at", existing["created_at"])
        else:
            item.setdefault("created_at", utc_now().isoformat())
        item["updated_at"] = utc_now().isoformat()
        model = model_cls.model_validate(item)
        record = model.model_dump(mode="json")
        path = self.object_path(model.object_type, model.id)
        write_json_atomic(path, record)
        self._sync_object(record, path)
        return record

    def get(self, object_id: str) -> dict[str, Any]:
        row = self._fetch_manifest_row(object_id)
        if row is None:
            raise NotFoundError(f"KB object not found: {object_id}")
        return read_json(Path(row["file_path"]))

    def related(self, object_id: str) -> dict[str, Any]:
        obj = self.get(object_id)
        related_objects = []
        for related_id in obj.get("related_ids", []):
            try:
                related = self.get(related_id)
            except NotFoundError:
                continue
            related_objects.append(
                {
                    "id": related["id"],
                    "object_type": related["object_type"],
                    "title": related["title"],
                    "summary": related.get("summary"),
                    "status": related.get("status"),
                }
            )
        return {"id": object_id, "related": related_objects}

    def search(
        self,
        *,
        query: str = "",
        object_types: Optional[Iterable[str]] = None,
        domain_tags: Optional[List[str]] = None,
        version: Optional[str] = None,
        scope: Optional[Union[Scope, str]] = None,
        status: Optional[Union[KBStatus, str]] = None,
        limit: int = 10,
        env_filters: Optional[Dict[str, str]] = None,
    ) -> SearchResponse:
        object_types = list(object_types or [])
        domain_tags = domain_tags or []
        env_filters = env_filters or {}

        rows = self._search_rows(query=query, object_types=object_types, scope=scope, status=status, limit=limit * 4)
        hits: list[SearchHit] = []
        warnings: list[str] = []
        normalized_query = query.strip().lower()
        for row in rows:
            item = read_json(Path(row["file_path"]))
            if domain_tags and not set(domain_tags).issubset(set(item.get("domain_tags", []))):
                continue
            object_version = item.get("version") or (item.get("metadata", {}) or {}).get("version")
            if version and object_version != version:
                if _is_exact_lookup(normalized_query, item):
                    warnings.append(
                        f"Version mismatch for {item['id']}: requested {version}, found {object_version or 'unspecified'}"
                    )
                else:
                    continue
            if env_filters and item.get("object_type") == "case":
                env = item.get("env", {}) or {}
                if any(env.get(key) != value for key, value in env_filters.items()):
                    continue
            hits.append(
                SearchHit(
                    id=item["id"],
                    object_type=item["object_type"],
                    title=item["title"],
                    summary=item.get("summary"),
                    score=max(float(row["score"]), 0.0),
                    status=item.get("status"),
                    tags=item.get("domain_tags", []),
                    source_refs=item.get("source_refs", []),
                )
            )
            if len(hits) >= limit:
                break
        return SearchResponse(query=query, hits=hits, warnings=sorted(set(warnings)))

    def rebuild_index(self) -> int:
        with self._connect() as conn:
            conn.execute("DELETE FROM kb_objects")
            conn.execute("DELETE FROM kb_objects_fts")
            conn.commit()

        count = 0
        for object_type, dir_name in OBJECT_DIRS.items():
            for path in sorted((self.canonical_root / dir_name).glob("*.json")):
                payload = read_json(path)
                model = OBJECT_MODELS[object_type].model_validate(payload)
                self._sync_object(model.model_dump(mode="json"), path)
                count += 1
        return count

    def object_path(self, object_type: str, object_id: str) -> Path:
        dir_name = OBJECT_DIRS.get(object_type)
        if dir_name is None:
            raise ValidationError(f"Unsupported KB object type: {object_type}")
        return self.canonical_root / dir_name / f"{object_id}.json"

    def _init_db(self) -> None:
        ensure_dir(self.db_path.parent)
        with self._connect() as conn:
            conn.executescript(MANIFEST_SQL)
            conn.commit()

    def _sync_object(self, payload: dict[str, Any], path: Path) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM kb_objects WHERE id = ?", (payload["id"],))
            conn.execute("DELETE FROM kb_objects_fts WHERE id = ?", (payload["id"],))
            conn.execute(
                """
                INSERT INTO kb_objects (
                  id, object_type, title, summary, scope, status, trust_level,
                  domain_tags_json, stack_tags_json, source_refs_json, related_ids_json,
                  file_path, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["id"],
                    payload["object_type"],
                    payload["title"],
                    payload.get("summary"),
                    payload["scope"],
                    payload["status"],
                    payload["trust_level"],
                    json.dumps(payload.get("domain_tags", [])),
                    json.dumps(payload.get("stack_tags", [])),
                    json.dumps(payload.get("source_refs", [])),
                    json.dumps(payload.get("related_ids", [])),
                    str(path),
                    payload["updated_at"],
                ),
            )
            conn.execute(
                """
                INSERT INTO kb_objects_fts (id, object_type, title, summary, body_text, domain_tags, stack_tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["id"],
                    payload["object_type"],
                    payload["title"],
                    payload.get("summary"),
                    _body_text(payload),
                    " ".join(payload.get("domain_tags", [])),
                    " ".join(payload.get("stack_tags", [])),
                ),
            )
            conn.commit()

    def _search_rows(
        self,
        *,
        query: str,
        object_types: list[str],
        scope: Optional[Union[Scope, str]],
        status: Optional[Union[KBStatus, str]],
        limit: int,
    ) -> list[sqlite3.Row]:
        clauses: list[str] = []
        params: list[Any] = []
        scope_value = scope.value if isinstance(scope, Scope) else scope
        status_value = status.value if isinstance(status, KBStatus) else status
        if object_types:
            placeholders = ", ".join("?" for _ in object_types)
            clauses.append(f"o.object_type IN ({placeholders})")
            params.extend(object_types)
        if scope_value:
            clauses.append("o.scope = ?")
            params.append(scope_value)
        if status_value:
            clauses.append("o.status = ?")
            params.append(status_value)

        with self._connect() as conn:
            if query.strip():
                sql = """
                    SELECT o.*, bm25(kb_objects_fts) AS score
                    FROM kb_objects AS o
                    JOIN kb_objects_fts ON kb_objects_fts.id = o.id
                    WHERE kb_objects_fts MATCH ?
                """
                params = [_fts_query(query)] + params
            else:
                sql = "SELECT o.*, 1.0 AS score FROM kb_objects AS o WHERE 1 = 1"

            if clauses:
                sql += " AND " + " AND ".join(clauses)
            sql += " ORDER BY score LIMIT ?"
            params.append(limit)
            return list(conn.execute(sql, params).fetchall())

    def _fetch_manifest_row(self, object_id: str) -> Optional[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM kb_objects WHERE id = ?", (object_id,)).fetchone()

    def _find_existing(self, object_id: str) -> Optional[dict[str, Any]]:
        row = self._fetch_manifest_row(object_id)
        if row is None:
            return None
        return read_json(Path(row["file_path"]))

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


def _body_text(payload: dict[str, Any]) -> str:
    chunks: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, str):
            chunks.append(value)
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, dict):
            for nested in value.values():
                visit(nested)

    visit(payload)
    return "\n".join(chunks)


def _is_exact_lookup(query: str, item: dict[str, Any]) -> bool:
    if not query:
        return False
    return query in {str(item.get("id", "")).lower(), str(item.get("title", "")).lower()}


def _fts_query(query: str) -> str:
    escaped = query.replace('"', '""').strip()
    return f'"{escaped}"'


def _default_paths() -> tuple[Path, Path]:
    repo_root = Path(__file__).resolve().parents[2]
    kb_root = repo_root / "kb"
    return kb_root, kb_root / "manifest.sqlite3"


if __name__ == "__main__":
    kb_root, db_path = _default_paths()
    store = ThinKBStore(kb_root=kb_root, db_path=db_path)
    count = store.rebuild_index()
    print(f"Rebuilt Thin KB index with {count} object(s)")
