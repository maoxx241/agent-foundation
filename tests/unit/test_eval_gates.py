from __future__ import annotations

import json

from packages.core.eval.gates import (
    _directory_matches,
    build_release_check_report,
    check_contract_drift,
    evaluate_comparison_thresholds,
    evaluate_eval_thresholds,
)
from packages.core.schemas import ComparisonReport, EvalRun, EvalThresholds, MetricThreshold, ReplayCaseResult, RetrievalCaseResult, WorkflowMetrics


def test_eval_thresholds_flag_metric_and_case_count_failures():
    run = EvalRun(
        run_id="candidate",
        generated_at="2026-03-10T00:00:00+00:00",
        retrieval_results=[RetrievalCaseResult(case_id="gold-1", expected_ids=["claim-a"], actual_ids=[])],
        replay_results=[ReplayCaseResult(case_id="replay-1", kind="workflow", task_ids=["task-a"], ok=True)],
    )
    thresholds = EvalThresholds(
        profile="smoke",
        min_gold_cases=2,
        min_replay_cases=2,
        retrieval=[MetricThreshold(metric="hit_at_1", op=">=", value=0.5)],
    )

    failures = evaluate_eval_thresholds(run, thresholds)

    assert {failure.check for failure in failures} == {"gold_cases", "replay_cases", "retrieval"}


def test_comparison_thresholds_flag_regressions():
    report = ComparisonReport(
        baseline_run_id="baseline",
        candidate_run_id="candidate",
        metric_deltas={},
        regressed_case_ids=["gold-1"],
        new_critical_failures=["candidate:/v1/kb/search/hybrid"],
        threshold_failures=[],
        baseline_missing=False,
        overall_status="regression",
    )
    thresholds = EvalThresholds(
        profile="smoke",
        max_regressed_case_count=0,
        max_new_critical_failures=0,
    )

    failures = evaluate_comparison_thresholds(report, thresholds)

    assert {failure.metric for failure in failures} == {"regressed_case_ids", "new_critical_failures"}


def test_release_check_report_blocks_when_baseline_required_but_missing():
    run = EvalRun(
        run_id="candidate",
        generated_at="2026-03-10T00:00:00+00:00",
        retrieval_results=[RetrievalCaseResult(case_id="gold-1", expected_ids=["claim-a"], actual_ids=["claim-a"])],
        replay_results=[ReplayCaseResult(case_id="replay-1", kind="workflow", task_ids=["task-a"], ok=True)],
        workflow_metrics=WorkflowMetrics(cases_total=1, design_acceptance_rate=1.0),
    )
    comparison = ComparisonReport(
        baseline_run_id="",
        candidate_run_id="candidate",
        metric_deltas={},
        regressed_case_ids=[],
        new_critical_failures=[],
        threshold_failures=[],
        baseline_missing=True,
        overall_status="no_baseline",
    )
    thresholds = EvalThresholds(profile="full", require_baseline=True)

    report = build_release_check_report(
        run=run,
        profile="full",
        contract_drift=False,
        comparison=comparison,
        thresholds=thresholds,
        started_at="2026-03-10T00:00:00+00:00",
        ended_at="2026-03-10T00:00:01+00:00",
    )

    assert report.overall_status == "blocked"
    assert report.threshold_failures


def test_directory_matches_rejects_stale_extra_files(tmp_path):
    root = tmp_path / "contracts"
    root.mkdir()
    (root / "artifact.json").write_text('{"ok": true}\n', encoding="utf-8")
    (root / "stale.json").write_text('{"stale": true}\n', encoding="utf-8")

    assert _directory_matches({"artifact.json": {"ok": True}}, root) is False


def test_check_contract_drift_ignores_generated_drift(tmp_path, monkeypatch):
    contracts = tmp_path / "contracts"
    generated = tmp_path / "generated"
    expected_openapi = {"artifact_api.v1.json": {"openapi": "3.1.0"}}
    expected_jsonschema = {"artifact_models.v1.json": {"bundle": "artifact_models.v1"}}

    _write_contract_tree(contracts / "openapi", expected_openapi)
    _write_contract_tree(contracts / "jsonschema", expected_jsonschema)
    _write_contract_tree(generated / "openapi", {"artifact_api.v1.json": {"openapi": "stale"}})
    _write_contract_tree(generated / "jsonschema", {"artifact_models.v1.json": {"bundle": "stale"}})

    monkeypatch.setattr("packages.core.eval.gates.contracts_root", lambda: contracts)
    monkeypatch.setattr("packages.core.eval.gates.build_openapi_contracts", lambda: expected_openapi)
    monkeypatch.setattr("packages.core.eval.gates.build_jsonschema_contracts", lambda: expected_jsonschema)

    assert check_contract_drift() is False


def test_check_contract_drift_rejects_contract_content_mismatch(tmp_path, monkeypatch):
    contracts = tmp_path / "contracts"
    expected_openapi = {"artifact_api.v1.json": {"openapi": "3.1.0"}}
    expected_jsonschema = {"artifact_models.v1.json": {"bundle": "artifact_models.v1"}}

    _write_contract_tree(contracts / "openapi", {"artifact_api.v1.json": {"openapi": "stale"}})
    _write_contract_tree(contracts / "jsonschema", expected_jsonschema)

    monkeypatch.setattr("packages.core.eval.gates.contracts_root", lambda: contracts)
    monkeypatch.setattr("packages.core.eval.gates.build_openapi_contracts", lambda: expected_openapi)
    monkeypatch.setattr("packages.core.eval.gates.build_jsonschema_contracts", lambda: expected_jsonschema)

    assert check_contract_drift() is True


def test_check_contract_drift_rejects_missing_or_extra_contract_files(tmp_path, monkeypatch):
    contracts = tmp_path / "contracts"
    expected_openapi = {"artifact_api.v1.json": {"openapi": "3.1.0"}}
    expected_jsonschema = {"artifact_models.v1.json": {"bundle": "artifact_models.v1"}}

    _write_contract_tree(contracts / "openapi", expected_openapi)
    _write_contract_tree(
        contracts / "jsonschema",
        {
            "artifact_models.v1.json": {"bundle": "artifact_models.v1"},
            "stale.json": {"bundle": "stale"},
        },
    )
    (contracts / "openapi" / "artifact_api.v1.json").unlink()

    monkeypatch.setattr("packages.core.eval.gates.contracts_root", lambda: contracts)
    monkeypatch.setattr("packages.core.eval.gates.build_openapi_contracts", lambda: expected_openapi)
    monkeypatch.setattr("packages.core.eval.gates.build_jsonschema_contracts", lambda: expected_jsonschema)

    assert check_contract_drift() is True


def _write_contract_tree(root, payloads):
    root.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (root / name).write_text(json.dumps(payload), encoding="utf-8")
