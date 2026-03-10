from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import Field

from .common import BaseSchema, EnvTuple, Reference, StorageIdentifier, TaskState, Timestamped


class VersionedArtifact(Timestamped):
    artifact_schema_version: str = "1.0"


class TaskBrief(VersionedArtifact):
    task_id: StorageIdentifier
    project_id: str
    title: str
    goal: str
    description: Optional[str] = None
    requester: Optional[str] = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    domain_tags: List[str] = Field(default_factory=list)
    env: EnvTuple = Field(default_factory=EnvTuple)
    acceptance_hint: Optional[str] = None
    initial_refs: List[Reference] = Field(default_factory=list)


class TaskStateRecord(VersionedArtifact):
    task_id: str
    state: TaskState
    previous_state: Optional[TaskState] = None
    changed_by: str
    reason: Optional[str] = None


class EvidencePack(VersionedArtifact):
    task_id: str
    summary: str
    relevant_refs: List[Reference] = Field(default_factory=list)
    claims: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    freshness_warnings: List[str] = Field(default_factory=list)
    env: EnvTuple = Field(default_factory=EnvTuple)


class DesignOption(BaseSchema):
    name: str
    summary: str
    assumptions: List[str] = Field(default_factory=list)
    tradeoffs: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    required_tests: List[str] = Field(default_factory=list)


class DesignSpec(VersionedArtifact):
    task_id: str
    objective: str
    constraints: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    selected_option: str
    options: List[DesignOption] = Field(default_factory=list)
    invariants: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)


class DesignReview(VersionedArtifact):
    task_id: str
    verdict: Literal["approve", "approve_with_conditions", "reject"]
    major_issues: List[str] = Field(default_factory=list)
    minor_issues: List[str] = Field(default_factory=list)
    required_changes: List[str] = Field(default_factory=list)
    unresolved_risks: List[str] = Field(default_factory=list)


class TestCase(BaseSchema):
    name: str
    purpose: str
    category: Literal[
        "functional",
        "orthogonal",
        "regression",
        "compatibility",
        "performance",
        "failure_mode",
    ]
    preconditions: List[str] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    expected_outcome: str


class TestSpec(VersionedArtifact):
    task_id: str
    strategy_summary: str
    invariants: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    cases: List[TestCase] = Field(default_factory=list)
    required_artifacts: List[str] = Field(default_factory=list)


class PatchBundle(VersionedArtifact):
    task_id: str
    patch_ref: Optional[str] = None
    changed_files: List[str] = Field(default_factory=list)
    summary: str
    implementation_notes: List[str] = Field(default_factory=list)
    known_gaps: List[str] = Field(default_factory=list)


class SelfTestReport(VersionedArtifact):
    task_id: str
    commands_run: List[str] = Field(default_factory=list)
    passed: bool
    summary: str
    covered_scope: List[str] = Field(default_factory=list)
    known_gaps: List[str] = Field(default_factory=list)
    artifacts: List[Reference] = Field(default_factory=list)


class ImplReview(VersionedArtifact):
    task_id: str
    verdict: Literal["approve", "approve_with_conditions", "reject"]
    spec_deviations: List[str] = Field(default_factory=list)
    implementation_risks: List[str] = Field(default_factory=list)
    test_coverage_concerns: List[str] = Field(default_factory=list)
    required_fixes: List[str] = Field(default_factory=list)


class ValidationReport(VersionedArtifact):
    task_id: str
    passed: bool
    summary: str
    functional_result: Optional[str] = None
    regression_result: Optional[str] = None
    performance_result: Optional[str] = None
    compatibility_result: Optional[str] = None
    findings: List[str] = Field(default_factory=list)
    root_cause_classification: Optional[
        Literal["implementation_defect", "design_ambiguity", "testspec_weakness", "environment_issue"]
    ] = None
    artifacts: List[Reference] = Field(default_factory=list)


class ADR(VersionedArtifact):
    task_id: str
    title: str
    context: str
    decision: str
    alternatives: List[str] = Field(default_factory=list)
    tradeoffs: List[str] = Field(default_factory=list)
    consequences: List[str] = Field(default_factory=list)


class ExperiencePacket(VersionedArtifact):
    task_id: str
    project_id: str
    summary: str
    env: EnvTuple = Field(default_factory=EnvTuple)
    root_cause: Optional[str] = None
    fix_summary: Optional[str] = None
    validation_summary: str
    related_artifacts: List[Reference] = Field(default_factory=list)
    candidate_claims: List[str] = Field(default_factory=list)
    candidate_procedures: List[str] = Field(default_factory=list)
    candidate_cases: List[str] = Field(default_factory=list)
    candidate_decisions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
