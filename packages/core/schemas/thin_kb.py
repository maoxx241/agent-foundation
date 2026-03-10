from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import Field

from .common import EnvTuple, KBStatus, Scope, StorageIdentifier, Timestamped, TrustLevel


class KBObject(Timestamped):
    id: StorageIdentifier
    object_type: str
    title: str
    summary: Optional[str] = None
    schema_version: str = "1.0"
    object_revision: int = Field(default=1, ge=1)
    version: Optional[str] = None
    scope: Scope = Scope.domain
    status: KBStatus = KBStatus.candidate
    trust_level: TrustLevel = TrustLevel.medium
    domain_tags: List[str] = Field(default_factory=list)
    stack_tags: List[str] = Field(default_factory=list)
    source_refs: List[str] = Field(default_factory=list)
    related_ids: List[str] = Field(default_factory=list)
    supersedes: List[str] = Field(default_factory=list)
    deprecated_reason: Optional[str] = None
    promotion_source: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Claim(KBObject):
    object_type: Literal["claim"] = "claim"
    subject: str
    predicate: str
    object: Optional[str] = None
    object_value: Optional[str] = None
    statement: str
    condition: Optional[str] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    env: Optional[EnvTuple] = None


class Procedure(KBObject):
    object_type: Literal["procedure"] = "procedure"
    goal: str
    preconditions: List[str] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    expected_outcomes: List[str] = Field(default_factory=list)
    rollback_steps: List[str] = Field(default_factory=list)
    failure_modes: List[str] = Field(default_factory=list)


class Case(KBObject):
    object_type: Literal["case"] = "case"
    case_type: Literal["incident", "benchmark", "experiment", "failure_analysis", "migration"]
    symptom: Optional[str] = None
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    env: EnvTuple = Field(default_factory=EnvTuple)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    outcome: Optional[str] = None


class Decision(KBObject):
    object_type: Literal["decision"] = "decision"
    context: str
    decision: str
    alternatives: List[str] = Field(default_factory=list)
    tradeoffs: List[str] = Field(default_factory=list)
    consequences: List[str] = Field(default_factory=list)
