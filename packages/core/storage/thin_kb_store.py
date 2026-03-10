from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Type, Union

from packages.core.migrations.registry import apply_kb_payload_migrations
from packages.core.schemas import Case, Claim, Decision, Procedure, SearchHit, SearchResponse
from packages.core.schemas.common import KBStatus, Scope
from packages.core.schemas.thin_kb import KBObject
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

STORAGE_TIERS = {"canonical", "candidate", "deprecated"}

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
  schema_version TEXT NOT NULL DEFAULT '1.0',
  object_revision INTEGER NOT NULL DEFAULT 1,
  supersedes_json TEXT NOT NULL DEFAULT '[]',
  deprecated_reason TEXT,
  promotion_source_json TEXT NOT NULL DEFAULT '{}',
  storage_tier TEXT NOT NULL DEFAULT 'canonical',
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
        self.candidates_root = self.kb_root / "candidates"
        self.deprecated_root = self.kb_root / "deprecated"
        self.db_path = db_path or self.kb_root / "manifest.sqlite3"
        for tier_root in (self.canonical_root, self.candidates_root, self.deprecated_root):
            for dir_name in OBJECT_DIRS.values():
                ensure_dir(tier_root / dir_name)
        self._init_db()

    def upsert(self, payload: dict[str, Any], storage_tier: Optional[str] = None) -> dict[str, Any]:
        object_type = str(payload.get("object_type", "")).strip()
        model_cls = OBJECT_MODELS.get(object_type)
        if model_cls is None:
            raise ValidationError(f"Unsupported KB object type: {object_type}")

        item, _ = apply_kb_payload_migrations(payload)
        inferred_tier = storage_tier or _infer_storage_tier(item)
        self._validate_storage_tier(inferred_tier)

        existing_row = self._fetch_manifest_row(str(item.get("id", ""))) if item.get("id") else None
        existing = self._load_object_from_row(existing_row) if existing_row is not None else None
        if existing and "created_at" in existing:
            item.setdefault("created_at", existing["created_at"])
            item["object_revision"] = int(existing.get("object_revision", 1)) + 1
        else:
            item.setdefault("created_at", utc_now().isoformat())
        item["updated_at"] = utc_now().isoformat()
        item["status"] = _normalize_status(item.get("status"), inferred_tier)
        if inferred_tier != "deprecated":
            item["deprecated_reason"] = None
        if inferred_tier == "canonical":
            item.setdefault("promotion_source", {})

        model = model_cls.model_validate(item)
        record = model.model_dump(mode="json")
        path = self.object_path(model.object_type, model.id, inferred_tier)
        previous_path = Path(existing_row["file_path"]) if existing_row is not None else None
        write_json_atomic(path, record)
        self._sync_object(record, path, inferred_tier)
        if previous_path is not None and previous_path != path and previous_path.exists():
            previous_path.unlink()
        return record

    def create_candidate(self, payload: dict[str, Any]) -> dict[str, Any]:
        item = dict(payload)
        item["status"] = KBStatus.candidate.value
        return self.upsert(item, storage_tier="candidate")

    def promote_candidate(self, candidate_id: str, *, promoted_by: str, reason: Optional[str] = None) -> dict[str, Any]:
        row = self._fetch_manifest_row(candidate_id)
        if row is None:
            raise NotFoundError(f"KB object not found: {candidate_id}")
        if row["storage_tier"] != "candidate":
            raise ValidationError(f"KB object is not a candidate: {candidate_id}")

        item = self._load_object_from_row(row)
        promotion_source = dict(item.get("promotion_source", {}))
        promotion_source.update(
            {
                "promoted_by": promoted_by,
                "promoted_at": utc_now().isoformat(),
                "promotion_reason": reason,
                "source_candidate_id": candidate_id,
            }
        )
        item["promotion_source"] = promotion_source
        item["status"] = KBStatus.trusted.value
        item["deprecated_reason"] = None
        promoted = self.upsert(item, storage_tier="canonical")
        candidate_path = Path(row["file_path"])
        if candidate_path.exists():
            candidate_path.unlink()
        return promoted

    def deprecate_object(
        self,
        object_id: str,
        *,
        deprecated_by: str,
        reason: str,
        superseded_by: str | None = None,
    ) -> dict[str, Any]:
        row = self._fetch_manifest_row(object_id)
        if row is None:
            raise NotFoundError(f"KB object not found: {object_id}")
        if row["storage_tier"] == "deprecated":
            raise ValidationError(f"KB object is already deprecated: {object_id}")

        item = self._load_object_from_row(row)
        item["status"] = KBStatus.deprecated.value
        item["deprecated_reason"] = reason
        promotion_source = dict(item.get("promotion_source", {}))
        promotion_source.update(
            {
                "deprecated_by": deprecated_by,
                "deprecated_at": utc_now().isoformat(),
            }
        )
        if superseded_by:
            promotion_source["superseded_by"] = superseded_by
        item["promotion_source"] = promotion_source
        deprecated = self.upsert(item, storage_tier="deprecated")
        previous_path = Path(row["file_path"])
        if previous_path.exists():
            previous_path.unlink()
        return deprecated

    def get(self, object_id: str) -> dict[str, Any]:
        row = self._fetch_manifest_row(object_id)
        if row is None:
            raise NotFoundError(f"KB object not found: {object_id}")
        return self._load_object_from_row(row)

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
            item = self._load_object_from_row(row)
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
        for storage_tier, tier_root in self._tier_roots().items():
            for object_type, dir_name in OBJECT_DIRS.items():
                for path in sorted((tier_root / dir_name).glob("*.json")):
                    payload = read_json(path)
                    payload, applied = apply_kb_payload_migrations(payload)
                    if applied:
                        write_json_atomic(path, payload)
                    model = OBJECT_MODELS[object_type].model_validate(payload)
                    self._sync_object(model.model_dump(mode="json"), path, storage_tier)
                    count += 1
        return count

    def object_path(self, object_type: str, object_id: str, storage_tier: str = "canonical") -> Path:
        self._validate_storage_tier(storage_tier)
        dir_name = OBJECT_DIRS.get(object_type)
        if dir_name is None:
            raise ValidationError(f"Unsupported KB object type: {object_type}")
        return self._tier_roots()[storage_tier] / dir_name / f"{object_id}.json"

    def _init_db(self) -> None:
        ensure_dir(self.db_path.parent)
        with self._connect() as conn:
            conn.executescript(MANIFEST_SQL)
            self._ensure_manifest_columns(conn)
            conn.commit()

    def _ensure_manifest_columns(self, conn: sqlite3.Connection) -> None:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(kb_objects)").fetchall()}
        alter_statements = {
            "schema_version": "ALTER TABLE kb_objects ADD COLUMN schema_version TEXT NOT NULL DEFAULT '1.0'",
            "object_revision": "ALTER TABLE kb_objects ADD COLUMN object_revision INTEGER NOT NULL DEFAULT 1",
            "supersedes_json": "ALTER TABLE kb_objects ADD COLUMN supersedes_json TEXT NOT NULL DEFAULT '[]'",
            "deprecated_reason": "ALTER TABLE kb_objects ADD COLUMN deprecated_reason TEXT",
            "promotion_source_json": "ALTER TABLE kb_objects ADD COLUMN promotion_source_json TEXT NOT NULL DEFAULT '{}'",
            "storage_tier": "ALTER TABLE kb_objects ADD COLUMN storage_tier TEXT NOT NULL DEFAULT 'canonical'",
        }
        for column, statement in alter_statements.items():
            if column not in columns:
                conn.execute(statement)

    def _sync_object(self, payload: dict[str, Any], path: Path, storage_tier: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM kb_objects WHERE id = ?", (payload["id"],))
            conn.execute("DELETE FROM kb_objects_fts WHERE id = ?", (payload["id"],))
            conn.execute(
                """
                INSERT INTO kb_objects (
                  id, object_type, title, summary, scope, status, trust_level,
                  domain_tags_json, stack_tags_json, source_refs_json, related_ids_json,
                  schema_version, object_revision, supersedes_json, deprecated_reason,
                  promotion_source_json, storage_tier, file_path, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    payload.get("schema_version", "1.0"),
                    int(payload.get("object_revision", 1)),
                    json.dumps(payload.get("supersedes", [])),
                    payload.get("deprecated_reason"),
                    json.dumps(payload.get("promotion_source", {})),
                    storage_tier,
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

    def _load_object_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        path = Path(row["file_path"])
        payload = read_json(path)
        payload, applied = apply_kb_payload_migrations(payload)
        if applied:
            write_json_atomic(path, payload)
            self._sync_object(payload, path, row["storage_tier"])
        return payload

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _validate_storage_tier(self, storage_tier: str) -> None:
        if storage_tier not in STORAGE_TIERS:
            raise ValidationError(f"Unsupported storage tier: {storage_tier}")

    def _tier_roots(self) -> dict[str, Path]:
        return {
            "canonical": self.canonical_root,
            "candidate": self.candidates_root,
            "deprecated": self.deprecated_root,
        }


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


def _normalize_status(status: Any, storage_tier: str) -> str:
    if isinstance(status, KBStatus):
        status = status.value
    if storage_tier == "candidate":
        return KBStatus.candidate.value
    if storage_tier == "deprecated":
        return KBStatus.deprecated.value
    if status in {KBStatus.trusted.value, KBStatus.deprecated.value, KBStatus.candidate.value, KBStatus.raw.value}:
        return str(status)
    return KBStatus.candidate.value


def _infer_storage_tier(payload: dict[str, Any]) -> str:
    status = str(payload.get("status") or "").strip()
    return {
        KBStatus.candidate.value: "candidate",
        KBStatus.deprecated.value: "deprecated",
    }.get(status, "canonical")


def _default_paths() -> tuple[Path, Path]:
    from packages.core.config import kb_db_path, kb_root

    return kb_root(), kb_db_path()


if __name__ == "__main__":
    kb_root, db_path = _default_paths()
    store = ThinKBStore(kb_root=kb_root, db_path=db_path)
    count = store.rebuild_index()
    print(f"Rebuilt Thin KB index with {count} object(s)")
