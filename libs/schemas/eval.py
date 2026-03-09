from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import AliasChoices, Field

from .common import BaseSchema, KBStatus, Scope


class GoldQueryCase(BaseSchema):
    case_id: str
    kind: Literal["fact_lookup", "procedure", "troubleshooting", "design_support", "writeback_promotion"]
    query: str
    expected_ids: List[str] = Field(default_factory=list)
    version: Optional[str] = None
    domain_tags: List[str] = Field(default_factory=list)
    scope: Optional[Scope] = None
    status_filter: Optional[KBStatus] = None
    allow_abstain: bool = False


class ReplayTaskSeed(BaseSchema):
    task_id: str
    project_id: str
    title: str
    goal: str
    description: Optional[str] = None
    requester: Optional[str] = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    domain_tags: List[str] = Field(default_factory=list)
    env: Dict[str, Any] = Field(default_factory=dict)
    acceptance_hint: Optional[str] = None
    initial_refs: List[Dict[str, Any]] = Field(default_factory=list)


class ReplayArtifactSeed(BaseSchema):
    task_id: str
    stage: str
    name: str
    format: Literal["json", "markdown", "text"]
    content: Any


class ReplaySeed(BaseSchema):
    kb_objects: List[Dict[str, Any]] = Field(default_factory=list)
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    code_sources: List[Dict[str, Any]] = Field(default_factory=list)
    tasks: List[ReplayTaskSeed] = Field(default_factory=list)
    artifacts: List[ReplayArtifactSeed] = Field(default_factory=list)


class ReplayStep(BaseSchema):
    method: Literal["GET", "POST", "PUT", "PATCH"]
    path: str
    body: Optional[Dict[str, Any]] = Field(
        default=None,
        validation_alias=AliasChoices("json", "body"),
        serialization_alias="json",
    )
    expect_status: int
    expect_state: Optional[str] = None
    expect_contains: List[str] = Field(default_factory=list)


class ReplayExpectation(BaseSchema):
    final_states: Dict[str, str] = Field(default_factory=dict)
    promoted_object_min: int = 0
    warnings: List[str] = Field(default_factory=list)


class ReplayCase(BaseSchema):
    case_id: str
    kind: Literal["artifact", "workflow", "retrieval", "recovery", "security", "writeback"]
    seed: ReplaySeed = Field(default_factory=ReplaySeed)
    steps: List[ReplayStep] = Field(default_factory=list)
    expected: ReplayExpectation = Field(default_factory=ReplayExpectation)


class ShadowPilotManifest(BaseSchema):
    cases: List[ReplayCase] = Field(default_factory=list)


class RetrievalCaseResult(BaseSchema):
    case_id: str
    expected_ids: List[str] = Field(default_factory=list)
    actual_ids: List[str] = Field(default_factory=list)
    requested_version: Optional[str] = None
    top_hit_version: Optional[str] = None
    abstained: bool = False
    warnings: List[str] = Field(default_factory=list)


class ReplayStepResult(BaseSchema):
    method: str
    path: str
    status_code: int
    ok: bool
    target_state: Optional[str] = None
    state: Optional[str] = None
    promoted_object_count: int = 0
    body_excerpt: Optional[str] = None


class ReplayCaseResult(BaseSchema):
    case_id: str
    kind: str
    task_ids: List[str] = Field(default_factory=list)
    ok: bool
    final_states: Dict[str, str] = Field(default_factory=dict)
    steps: List[ReplayStepResult] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class RetrievalMetrics(BaseSchema):
    cases_total: int = 0
    hit_at_1: float = 0.0
    hit_at_3: float = 0.0
    hit_at_5: float = 0.0
    mrr: float = 0.0
    wrong_version_rate: float = 0.0
    false_positive_rate: float = 0.0
    abstain_precision: float = 0.0


class WorkflowMetrics(BaseSchema):
    cases_total: int = 0
    design_acceptance_rate: float = 0.0
    review_rejection_rate: float = 0.0
    validation_failure_rate: float = 0.0
    writeback_promotion_rate: float = 0.0
    human_intervention_rate: float = 0.0
    regression_escape_rate: float = 0.0


class EvalRun(BaseSchema):
    run_id: str
    generated_at: str
    retrieval_results: List[RetrievalCaseResult] = Field(default_factory=list)
    replay_results: List[ReplayCaseResult] = Field(default_factory=list)
    retrieval_metrics: RetrievalMetrics = Field(default_factory=RetrievalMetrics)
    workflow_metrics: WorkflowMetrics = Field(default_factory=WorkflowMetrics)
    report_dir: Optional[str] = None


class InterventionRecord(BaseSchema):
    run_id: str
    task_id: str
    stage: str
    issue_type: str
    severity: Literal["low", "medium", "high", "critical"]
    fix_type: str
    missing_plane: Literal["none", "memory", "kb", "artifact"]
    notes: Optional[str] = None
    timestamp: str
    resolved: bool = False


class RunSummary(BaseSchema):
    run_id: str
    started_at: str
    ended_at: str
    tasks_total: int
    task_terminal_states: Dict[str, int] = Field(default_factory=dict)
    retrieval_metrics: Dict[str, Any] = Field(default_factory=dict)
    workflow_metrics: Dict[str, Any] = Field(default_factory=dict)
    interventions_total: int = 0
    promoted_objects_total: int = 0
    critical_boundary_failures: List[str] = Field(default_factory=list)
    top_failure_modes: List[str] = Field(default_factory=list)


class ComparisonReport(BaseSchema):
    baseline_run_id: str
    candidate_run_id: str
    metric_deltas: Dict[str, float] = Field(default_factory=dict)
    regressed_case_ids: List[str] = Field(default_factory=list)
    new_critical_failures: List[str] = Field(default_factory=list)
    overall_status: Literal["ok", "regression", "no_baseline"] = "ok"
