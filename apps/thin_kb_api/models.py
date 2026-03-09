from __future__ import annotations

from typing import Optional

from pydantic import Field

from libs.schemas.common import BaseSchema, KBStatus, Scope


class KBSearchRequest(BaseSchema):
    query: str = ""
    object_types: list[str] = Field(default_factory=list)
    domain_tags: list[str] = Field(default_factory=list)
    version: Optional[str] = None
    status: Optional[KBStatus] = None
    scope: Optional[Scope] = None
    limit: int = Field(default=10, ge=1, le=100)
    env_filters: dict[str, str] = Field(default_factory=dict)


class DocumentIngestRequest(BaseSchema):
    title: Optional[str] = None
    path: Optional[str] = None
    content: Optional[str] = None
    content_type: Optional[str] = None
    language: Optional[str] = None
    domain_tags: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class CodeIngestRequest(BaseSchema):
    title: Optional[str] = None
    path: Optional[str] = None
    content: Optional[str] = None
    language: Optional[str] = None
    domain_tags: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class HybridSearchRequest(BaseSchema):
    query: str
    object_types: list[str] = Field(default_factory=list)
    source_types: list[str] = Field(default_factory=list)
    domain_tags: list[str] = Field(default_factory=list)
    version: Optional[str] = None
    status: Optional[KBStatus] = None
    scope: Optional[Scope] = None
    limit: int = Field(default=10, ge=1, le=100)
    env_filters: dict[str, str] = Field(default_factory=dict)


class RefineWritebackRequest(BaseSchema):
    task_id: Optional[str] = None
    experience_packet: Optional[dict[str, object]] = None
    persist: bool = False
