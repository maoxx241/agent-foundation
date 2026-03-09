from __future__ import annotations

import pytest

from libs.eval.metrics import compare_metric_maps, compute_retrieval_metrics, compute_workflow_metrics
from libs.schemas import ReplayCaseResult, ReplayStepResult, RetrievalCaseResult


def test_retrieval_metrics_capture_hits_false_positives_and_versions():
    metrics = compute_retrieval_metrics(
        [
            RetrievalCaseResult(
                case_id="case-1",
                expected_ids=["claim-a"],
                actual_ids=["claim-a", "claim-b"],
                requested_version="1.0.0",
                top_hit_version="1.0.0",
            ),
            RetrievalCaseResult(
                case_id="case-2",
                expected_ids=["claim-b"],
                actual_ids=["claim-x"],
                requested_version="2.0.0",
                top_hit_version="1.0.0",
            ),
            RetrievalCaseResult(
                case_id="case-3",
                expected_ids=[],
                actual_ids=[],
                abstained=True,
            ),
            RetrievalCaseResult(
                case_id="case-4",
                expected_ids=[],
                actual_ids=["noise-hit"],
            ),
        ]
    )

    assert metrics.cases_total == 4
    assert metrics.hit_at_1 == pytest.approx(0.25)
    assert metrics.hit_at_3 == pytest.approx(0.25)
    assert metrics.mrr == pytest.approx(0.25)
    assert metrics.wrong_version_rate == pytest.approx(0.5)
    assert metrics.false_positive_rate == pytest.approx(0.5)
    assert metrics.abstain_precision == pytest.approx(1.0)


def test_workflow_metrics_capture_rejections_promotions_and_interventions():
    replay_results = [
        ReplayCaseResult(
            case_id="workflow-ok",
            kind="workflow",
            task_ids=["task-ok"],
            ok=True,
            final_states={"task-ok": "WRITTEN_BACK"},
            steps=[
                ReplayStepResult(method="PATCH", path="/v1/tasks/task-ok/state", status_code=200, ok=True, target_state="DESIGN_APPROVED"),
                ReplayStepResult(method="PATCH", path="/v1/tasks/task-ok/state", status_code=200, ok=True, target_state="IMPL_APPROVED"),
                ReplayStepResult(method="PATCH", path="/v1/tasks/task-ok/state", status_code=200, ok=True, target_state="VALIDATED"),
                ReplayStepResult(method="POST", path="/v1/kb/writeback/refine", status_code=200, ok=True, promoted_object_count=2),
            ],
        ),
        ReplayCaseResult(
            case_id="workflow-fail",
            kind="workflow",
            task_ids=["task-fail"],
            ok=False,
            final_states={"task-fail": "IMPL_APPROVED"},
            steps=[
                ReplayStepResult(method="PATCH", path="/v1/tasks/task-fail/state", status_code=409, ok=True, target_state="DESIGN_APPROVED"),
                ReplayStepResult(method="PATCH", path="/v1/tasks/task-fail/state", status_code=409, ok=True, target_state="VALIDATED"),
            ],
        ),
    ]

    metrics = compute_workflow_metrics(
        replay_results,
        intervention_task_ids={"task-ok"},
        regression_escape_task_ids={"task-ok"},
    )

    assert metrics.cases_total == 2
    assert metrics.design_acceptance_rate == pytest.approx(0.5)
    assert metrics.review_rejection_rate == pytest.approx(0.0)
    assert metrics.validation_failure_rate == pytest.approx(0.5)
    assert metrics.writeback_promotion_rate == pytest.approx(1.0)
    assert metrics.human_intervention_rate == pytest.approx(0.5)
    assert metrics.regression_escape_rate == pytest.approx(1.0)


def test_compare_metric_maps_marks_regressions():
    report = compare_metric_maps(
        {"hit_at_1": 0.8, "wrong_version_rate": 0.1},
        {"hit_at_1": 0.5, "wrong_version_rate": 0.2},
    )

    assert report.overall_status == "regression"
    assert set(report.regressed_case_ids) == {"hit_at_1", "wrong_version_rate"}
