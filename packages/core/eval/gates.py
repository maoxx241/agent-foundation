from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from packages.core.config import contracts_root, generated_root, reports_root
from packages.core.contracts import build_jsonschema_contracts, build_openapi_contracts
from packages.core.schemas import ComparisonReport, EvalRun, EvalThresholds, ReleaseCheckReport, ThresholdFailure
from packages.core.storage.fs_utils import ensure_dir
from .corpora import load_eval_thresholds


def check_contract_drift() -> bool:
    expected_openapi = build_openapi_contracts()
    expected_jsonschema = build_jsonschema_contracts()
    frozen_openapi = contracts_root() / "openapi"
    frozen_jsonschema = contracts_root() / "jsonschema"
    generated_openapi = generated_root() / "openapi"
    generated_jsonschema = generated_root() / "jsonschema"

    comparisons = [
        _directory_matches(expected_openapi, frozen_openapi),
        _directory_matches(expected_openapi, generated_openapi),
        _directory_matches(expected_jsonschema, frozen_jsonschema),
        _directory_matches(expected_jsonschema, generated_jsonschema),
    ]
    return not all(comparisons)


def resolve_baseline_run_id(root: Path | None = None) -> str | None:
    explicit = os.getenv("AGENT_FOUNDATION_BASELINE_RUN_ID")
    if explicit:
        return explicit

    root = root or Path("evals")
    manifest_path = root / "manifests" / "baseline.json"
    if not manifest_path.exists():
        return None
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return payload.get("baseline_run_id")


def evaluate_eval_thresholds(run: EvalRun, thresholds: EvalThresholds) -> list[ThresholdFailure]:
    failures: list[ThresholdFailure] = []
    failures.extend(_check_case_count("gold", len(run.retrieval_results), thresholds.min_gold_cases))
    failures.extend(_check_case_count("replay", len(run.replay_results), thresholds.min_replay_cases))
    failures.extend(_check_threshold_group("retrieval", run.retrieval_metrics.model_dump(mode="json"), thresholds.retrieval))
    failures.extend(_check_threshold_group("workflow", run.workflow_metrics.model_dump(mode="json"), thresholds.workflow))
    return failures


def evaluate_comparison_thresholds(report: ComparisonReport, thresholds: EvalThresholds) -> list[ThresholdFailure]:
    failures: list[ThresholdFailure] = []
    if thresholds.require_baseline and (report.baseline_missing or not report.baseline_run_id):
        failures.append(
            ThresholdFailure(
                check="comparison",
                metric="baseline",
                op="required",
                expected=1,
                actual=0,
                message="Baseline run is required for this profile",
            )
        )
        return failures

    if report.baseline_missing or not report.baseline_run_id:
        return failures

    regressed_count = len(report.regressed_case_ids)
    if regressed_count > thresholds.max_regressed_case_count:
        failures.append(
            ThresholdFailure(
                check="comparison",
                metric="regressed_case_ids",
                op="<=",
                expected=float(thresholds.max_regressed_case_count),
                actual=float(regressed_count),
            )
        )
    new_failures = len(report.new_critical_failures)
    if new_failures > thresholds.max_new_critical_failures:
        failures.append(
            ThresholdFailure(
                check="comparison",
                metric="new_critical_failures",
                op="<=",
                expected=float(thresholds.max_new_critical_failures),
                actual=float(new_failures),
            )
        )
    return failures


def build_release_check_report(
    *,
    run: EvalRun,
    profile: str,
    contract_drift: bool,
    comparison: ComparisonReport | None,
    thresholds: EvalThresholds,
    started_at: str,
    ended_at: str,
    report_root: Path | None = None,
) -> ReleaseCheckReport:
    report_root = report_root or reports_root()
    threshold_failures = evaluate_eval_thresholds(run, thresholds)
    if comparison is not None:
        comparison_failures = evaluate_comparison_thresholds(comparison, thresholds)
        threshold_failures.extend(comparison_failures)
        comparison.threshold_failures = comparison_failures

    replay_ok = all(item.ok for item in run.replay_results)
    eval_ok = not threshold_failures
    overall_status = "ok"
    if contract_drift or not replay_ok or not eval_ok:
        overall_status = "failed"
    if thresholds.require_baseline and (comparison is None or comparison.baseline_missing):
        overall_status = "blocked"

    return ReleaseCheckReport(
        run_id=run.run_id,
        started_at=started_at,
        ended_at=ended_at,
        profile=profile,
        contract_drift=contract_drift,
        replay_ok=replay_ok,
        eval_ok=eval_ok,
        replay_report_dir=str((report_root / "replay" / run.run_id).resolve()),
        eval_report_dir=str((report_root / "eval" / run.run_id).resolve()),
        comparison_report_path=(
            str((report_root / "eval" / run.run_id / "comparison.json").resolve()) if comparison and comparison.baseline_run_id else None
        ),
        threshold_failures=threshold_failures,
        regressed_case_ids=list(comparison.regressed_case_ids) if comparison else [],
        new_critical_failures=list(comparison.new_critical_failures) if comparison else [],
        overall_status=overall_status,
    )


def load_threshold_profile(root: Path | None = None, *, path: Path | None = None, profile: str = "smoke") -> EvalThresholds:
    return load_eval_thresholds(root, path=path, profile=profile)


def _check_case_count(kind: str, actual: int, minimum: int) -> list[ThresholdFailure]:
    if actual >= minimum:
        return []
    return [
        ThresholdFailure(
            check=f"{kind}_cases",
            metric="count",
            op=">=",
            expected=float(minimum),
            actual=float(actual),
        )
    ]


def _check_threshold_group(group: str, metrics: dict[str, Any], thresholds: list[Any]) -> list[ThresholdFailure]:
    failures: list[ThresholdFailure] = []
    for threshold in thresholds:
        actual = float(metrics.get(threshold.metric, 0.0))
        if not _passes(actual, threshold.op, float(threshold.value)):
            failures.append(
                ThresholdFailure(
                    check=group,
                    metric=threshold.metric,
                    op=threshold.op,
                    expected=float(threshold.value),
                    actual=actual,
                )
            )
    return failures


def _directory_matches(expected: dict[str, dict[str, Any]], root: Path) -> bool:
    ensure_dir(root)
    for name, payload in expected.items():
        path = root / name
        if not path.exists():
            return False
        current = json.loads(path.read_text(encoding="utf-8"))
        if current != payload:
            return False
    return True


def _passes(actual: float, op: str, expected: float) -> bool:
    if op == ">=":
        return actual >= expected
    if op == "<=":
        return actual <= expected
    return actual == expected
