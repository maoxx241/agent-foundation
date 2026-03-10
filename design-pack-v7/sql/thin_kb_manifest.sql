-- Phase 1 Thin KB manifest/index schema

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
  stack_tags,
  content=''
);
