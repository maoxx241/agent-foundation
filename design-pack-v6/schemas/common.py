from __future__ import annotations

"""Common types for the Phase 1 agent-foundation design pack.

These models are intentionally conservative:
- They should be stable enough for Codex to implement directly.
- They should not assume Phase 2 parsing/retrieval infrastructure.
- They should be JSON-serializable and Git-friendly.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


class BaseSchema(BaseModel):
    """Base class with strict-ish, explicit behavior for API-facing models."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )


class Timestamped(BaseSchema):
    created_at: datetime
    updated_at: datetime


class Scope(str, Enum):
    user = "user"
    project = "project"
    session = "session"
    task = "task"
    global_ = "global"
    domain = "domain"


class TrustLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskState(str, Enum):
    NEW = "NEW"
    EVIDENCE_READY = "EVIDENCE_READY"
    DESIGN_APPROVED = "DESIGN_APPROVED"
    TESTSPEC_FROZEN = "TESTSPEC_FROZEN"
    IMPLEMENTED = "IMPLEMENTED"
    IMPL_APPROVED = "IMPL_APPROVED"
    VALIDATED = "VALIDATED"
    RELEASED = "RELEASED"
    WRITTEN_BACK = "WRITTEN_BACK"


class KBStatus(str, Enum):
    raw = "raw"
    candidate = "candidate"
    trusted = "trusted"
    deprecated = "deprecated"


class ArtifactStage(str, Enum):
    task = "00_task"
    evidence = "10_evidence"
    design = "20_design"
    test = "30_test"
    dev = "40_dev"
    review = "50_review"
    validation = "60_validation"
    release = "70_release"
    writeback = "80_writeback"


class EnvTuple(BaseSchema):
    os: Optional[str] = None
    python: Optional[str] = None
    project: Optional[str] = None
    repo: Optional[str] = None
    branch: Optional[str] = None
    commit: Optional[str] = None
    cann: Optional[str] = None
    torch: Optional[str] = None
    torch_npu: Optional[str] = None
    vllm: Optional[str] = None
    vllm_ascend: Optional[str] = None
    hardware: Optional[str] = None
    driver: Optional[str] = None
    extra: Dict[str, str] = Field(default_factory=dict)


class Reference(BaseSchema):
    id: str
    ref_type: Literal[
        "artifact",
        "memory",
        "claim",
        "procedure",
        "case",
        "decision",
        "source",
        "extract",
        "external",
    ]
    title: Optional[str] = None
    uri: Optional[str] = None
    notes: Optional[str] = None


class SearchQuery(BaseSchema):
    query: str
    scope: Optional[Scope] = None
    domain_tags: List[str] = Field(default_factory=list)
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    filters: Dict[str, Any] = Field(default_factory=dict)


class SearchHit(BaseSchema):
    id: str
    object_type: str
    title: str
    summary: Optional[str] = None
    score: float = Field(ge=0.0)
    status: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source_refs: List[str] = Field(default_factory=list)


class SearchResponse(BaseSchema):
    query: str
    hits: List[SearchHit] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
