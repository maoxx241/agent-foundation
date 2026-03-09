from __future__ import annotations

from typing import Any

from libs.schemas import ComparisonReport, ReplayCaseResult, RetrievalCaseResult, RetrievalMetrics, WorkflowMetrics


def compute_retrieval_metrics(results: list[RetrievalCaseResult]) -> RetrievalMetrics:
    total = len(results)
    if total == 0:
        return RetrievalMetrics()

    hit1 = hit3 = hit5 = 0
    mrr_total = 0.0
    wrong_version = 0
    wrong_version_total = 0
    false_positive = 0
    negative_total = 0
    abstain_true_positive = 0
    abstain_total = 0

    for result in results:
        expected = set(result.expected_ids)
        actual = result.actual_ids
        if expected:
            if any(item in expected for item in actual[:1]):
                hit1 += 1
            if any(item in expected for item in actual[:3]):
                hit3 += 1
            if any(item in expected for item in actual[:5]):
                hit5 += 1
            mrr_total += _mrr(expected, actual)
        else:
            negative_total += 1
            if actual:
                false_positive += 1

        if result.requested_version:
            wrong_version_total += 1
            if result.top_hit_version and result.top_hit_version != result.requested_version:
                wrong_version += 1

        if result.abstained:
            abstain_total += 1
            if not expected:
                abstain_true_positive += 1

    return RetrievalMetrics(
        cases_total=total,
        hit_at_1=_rate(hit1, total),
        hit_at_3=_rate(hit3, total),
        hit_at_5=_rate(hit5, total),
        mrr=round(mrr_total / total, 6),
        wrong_version_rate=_rate(wrong_version, wrong_version_total),
        false_positive_rate=_rate(false_positive, negative_total),
        abstain_precision=_rate(abstain_true_positive, abstain_total),
    )


def compute_workflow_metrics(
    replay_results: list[ReplayCaseResult],
    *,
    intervention_task_ids: set[str] | None = None,
    regression_escape_task_ids: set[str] | None = None,
) -> WorkflowMetrics:
    total = len(replay_results)
    if total == 0:
        return WorkflowMetrics()

    intervention_task_ids = intervention_task_ids or set()
    regression_escape_task_ids = regression_escape_task_ids or set()

    design_attempts = design_approvals = 0
    review_attempts = review_rejects = 0
    validation_attempts = validation_failures = 0
    writeback_attempts = writeback_promotions = 0
    written_back_tasks: set[str] = set()
    all_task_ids: set[str] = set()

    for result in replay_results:
        all_task_ids.update(result.task_ids)
        for step in result.steps:
            if step.path.endswith("/state") and step.method == "PATCH":
                if step.target_state == "DESIGN_APPROVED":
                    design_attempts += 1
                    if step.status_code == 200:
                        design_approvals += 1
                if step.target_state == "IMPL_APPROVED":
                    review_attempts += 1
                    if step.status_code >= 400:
                        review_rejects += 1
                if step.target_state == "VALIDATED":
                    validation_attempts += 1
                    if step.status_code >= 400:
                        validation_failures += 1
            if step.path.endswith("/writeback/refine"):
                writeback_attempts += 1
                if step.promoted_object_count > 0:
                    writeback_promotions += 1
        for task_id, state in result.final_states.items():
            all_task_ids.add(task_id)
            if state == "WRITTEN_BACK":
                written_back_tasks.add(task_id)

    return WorkflowMetrics(
        cases_total=total,
        design_acceptance_rate=_rate(design_approvals, design_attempts),
        review_rejection_rate=_rate(review_rejects, review_attempts),
        validation_failure_rate=_rate(validation_failures, validation_attempts),
        writeback_promotion_rate=_rate(writeback_promotions, writeback_attempts),
        human_intervention_rate=_rate(len(intervention_task_ids), len(all_task_ids)),
        regression_escape_rate=_rate(len(regression_escape_task_ids & written_back_tasks), len(written_back_tasks)),
    )


def compare_metric_maps(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> ComparisonReport:
    metric_deltas: dict[str, float] = {}
    regressions: list[str] = []
    for key in sorted(set(baseline) | set(candidate)):
        base_value = baseline.get(key)
        cand_value = candidate.get(key)
        if not isinstance(base_value, (int, float)) or not isinstance(cand_value, (int, float)):
            continue
        metric_deltas[key] = round(float(cand_value) - float(base_value), 6)
        if _is_regression_metric(key, base_value, cand_value):
            regressions.append(key)
    return ComparisonReport(
        baseline_run_id="",
        candidate_run_id="",
        metric_deltas=metric_deltas,
        regressed_case_ids=regressions,
        new_critical_failures=[],
        overall_status="regression" if regressions else "ok",
    )


def _mrr(expected: set[str], actual: list[str]) -> float:
    for index, item in enumerate(actual, start=1):
        if item in expected:
            return 1.0 / index
    return 0.0


def _is_regression_metric(metric: str, baseline: float, candidate: float) -> bool:
    lower_is_better = {
        "wrong_version_rate",
        "false_positive_rate",
        "human_intervention_rate",
        "validation_failure_rate",
        "review_rejection_rate",
        "regression_escape_rate",
    }
    if metric in lower_is_better:
        return candidate > baseline
    return candidate < baseline


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)
