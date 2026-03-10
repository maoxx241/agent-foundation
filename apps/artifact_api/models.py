from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import AliasChoices, Field

from packages.core.schemas.common import BaseSchema, EnvTuple, Reference, StorageIdentifier, TaskState


class CreateTaskRequest(BaseSchema):
    task_id: StorageIdentifier
    project_id: str
    title: str
    goal: str
    description: Optional[str] = None
    requester: Optional[str] = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    domain_tags: list[str] = Field(default_factory=list)
    env: EnvTuple = Field(default_factory=EnvTuple)
    acceptance_hint: Optional[str] = None
    initial_refs: list[Reference] = Field(default_factory=list)


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


CreateTaskRequest.model_rebuild()
UpdateTaskStateRequest.model_rebuild()
PutArtifactRequest.model_rebuild()
ArchiveTaskRequest.model_rebuild()
