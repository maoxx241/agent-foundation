from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import Field

from packages.core.schemas.common import BaseSchema


class LedgerEvent(BaseSchema):
    event_id: str
    entity_type: Literal["task", "kb", "audit", "replay_run", "release"]
    entity_id: str
    event_type: str
    actor: Optional[str] = None
    timestamp: str
    trace_id: Optional[str] = None
    run_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class TaskEvent(LedgerEvent):
    entity_type: Literal["task"] = "task"


class KBEvent(LedgerEvent):
    entity_type: Literal["kb"] = "kb"


class AuditEvent(LedgerEvent):
    entity_type: Literal["audit"] = "audit"


class ReplayRunEvent(LedgerEvent):
    entity_type: Literal["replay_run"] = "replay_run"


class ReleaseEvent(LedgerEvent):
    entity_type: Literal["release"] = "release"


class TaskAuditReport(BaseSchema):
    task_id: str
    current: Optional[Dict[str, Any]] = None
    events: List[LedgerEvent] = Field(default_factory=list)


class ObjectAuditReport(BaseSchema):
    object_id: str
    current: Optional[Dict[str, Any]] = None
    events: List[LedgerEvent] = Field(default_factory=list)
