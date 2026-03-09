from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import Field

from .common import BaseSchema, Timestamped


class SourceRecord(Timestamped):
    source_id: str
    source_type: Literal["document", "code"]
    title: str
    path: Optional[str] = None
    content_type: str
    language: Optional[str] = None
    parser: str
    checksum: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractedChunk(BaseSchema):
    chunk_id: str
    source_id: str
    chunk_type: Literal["section", "function", "class", "module", "paragraph", "snippet"]
    title: str
    content: str
    language: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractBundle(Timestamped):
    source_id: str
    source_type: Literal["document", "code"]
    title: str
    parser: str
    language: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    chunks: List[ExtractedChunk] = Field(default_factory=list)


class HybridSearchHit(BaseSchema):
    id: str
    hit_type: Literal["canonical", "extract"]
    title: str
    score: float = Field(ge=0.0)
    summary: Optional[str] = None
    snippet: Optional[str] = None
    object_type: Optional[str] = None
    source_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HybridSearchResponse(BaseSchema):
    query: str
    hits: List[HybridSearchHit] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class RefinedWriteback(Timestamped):
    task_id: str
    persisted: bool
    summary: str
    object_ids: List[str] = Field(default_factory=list)
    objects: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
