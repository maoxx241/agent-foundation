from __future__ import annotations

from typing import Any, Optional

from pydantic import AliasChoices, Field

from packages.core.schemas.common import BaseSchema, TaskState


class CreateTaskRequest(BaseSchema):
    task_id: str
    project_id: str
    title: str
    goal: str
    description: Optional[str] = None
    requester: Optional[str] = None
    priority: str = "medium"
    domain_tags: list[str] = Field(default_factory=list)
    env: dict[str, Any] = Field(default_factory=dict)
    acceptance_hint: Optional[str] = None
    initial_refs: list[dict[str, Any]] = Field(default_factory=list)


class UpdateTaskStateRequest(BaseSchema):
    target_state: TaskState = Field(validation_alias=AliasChoices("target_state", "state"))
    changed_by: str
    reason: Optional[str] = None


class PutArtifactRequest(BaseSchema):
    format: str
    content: Any


class ArchiveTaskRequest(BaseSchema):
    changed_by: str
    reason: Optional[str] = None
