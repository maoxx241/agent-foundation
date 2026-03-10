from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import Field

from packages.core.schemas.common import BaseSchema


class LedgerEvent(BaseSchema):
    event_id: str
    entity_type: Literal["task", "kb", "audit"]
    entity_id: str
    event_type: str
    actor: Optional[str] = None
    timestamp: str
    trace_id: Optional[str] = None
    run_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class TaskAuditReport(BaseSchema):
    task_id: str
    current: Optional[Dict[str, Any]] = None
    events: List[LedgerEvent] = Field(default_factory=list)


class ObjectAuditReport(BaseSchema):
    object_id: str
    current: Optional[Dict[str, Any]] = None
    events: List[LedgerEvent] = Field(default_factory=list)
