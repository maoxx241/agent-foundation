from __future__ import annotations

import os
from pathlib import Path

from dagster import (
    AssetCheckResult,
    AssetSelection,
    Definitions,
    RetryPolicy,
    ScheduleDefinition,
    asset,
    asset_check,
    define_asset_job,
)

from libs.eval.corpora import load_gold_cases, load_replay_cases
from libs.eval.reporting import compare_runs, default_reports_root, new_run_id, write_eval_run
from libs.eval.runner import EvaluationRunner
from libs.schemas import GoldQueryCase, ReplayCase


def _repo_root() -> Path:
    return Path(os.getenv("AGENT_FOUNDATION_REPO_ROOT", Path(__file__).resolve().parents[2])).resolve()


def _eval_root() -> Path:
    return Path(os.getenv("AGENT_FOUNDATION_EVAL_ROOT", _repo_root() / "eval")).resolve()


def _reports_root() -> Path:
    return Path(os.getenv("AGENT_FOUNDATION_REPORTS_ROOT", default_reports_root())).resolve()


def _run_id() -> str:
    return os.getenv("AGENT_FOUNDATION_RUN_ID", new_run_id("dagster"))


@asset(retry_policy=RetryPolicy(max_retries=1))
def gold_datasets() -> list[dict]:
    return [item.model_dump(mode="json") for item in load_gold_cases(_eval_root())]


@asset(retry_policy=RetryPolicy(max_retries=1))
def replay_corpus() -> list[dict]:
    return [item.model_dump(mode="json") for item in load_replay_cases(_eval_root())]


@asset(retry_policy=RetryPolicy(max_retries=1))
def replay_results(gold_datasets: list[dict], replay_corpus: list[dict]) -> dict:
    runner = EvaluationRunner(_repo_root())
    run = runner.run(
        gold_cases=[GoldQueryCase.model_validate(item) for item in gold_datasets],
        replay_cases=[ReplayCase.model_validate(item) for item in replay_corpus],
        run_id=_run_id(),
    )
    report_dir = write_eval_run(run, _reports_root())
    payload = run.model_dump(mode="json")
    payload["report_dir"] = str(report_dir)
    return payload


@asset
def retrieval_metrics(replay_results: dict) -> dict:
    return replay_results["retrieval_metrics"]


@asset
def workflow_metrics(replay_results: dict) -> dict:
    return replay_results["workflow_metrics"]


@asset
def eval_report(replay_results: dict, retrieval_metrics: dict, workflow_metrics: dict) -> dict:
    return {
        "run_id": replay_results["run_id"],
        "generated_at": replay_results["generated_at"],
        "report_dir": replay_results["report_dir"],
        "retrieval_metrics": retrieval_metrics,
        "workflow_metrics": workflow_metrics,
    }


@asset
def comparison_report(eval_report: dict) -> dict:
    baseline_run_id = os.getenv("AGENT_FOUNDATION_BASELINE_RUN_ID")
    if not baseline_run_id:
        return {
            "baseline_run_id": "",
            "candidate_run_id": eval_report["run_id"],
            "metric_deltas": {},
            "regressed_case_ids": [],
            "new_critical_failures": [],
            "overall_status": "no_baseline",
        }
    report = compare_runs(
        _reports_root() / "eval" / baseline_run_id,
        _reports_root() / "eval" / eval_report["run_id"],
        _reports_root() / "eval" / eval_report["run_id"] / "comparison.json",
    )
    return report.model_dump(mode="json")


@asset_check(asset=gold_datasets)
def gold_dataset_check(gold_datasets: list[dict]) -> AssetCheckResult:
    passed = validate_gold_dataset_payload(gold_datasets)
    return AssetCheckResult(
        passed=passed,
        metadata={"count": len(gold_datasets)},
    )


@asset_check(asset=replay_corpus)
def replay_corpus_check(replay_corpus: list[dict]) -> AssetCheckResult:
    passed = validate_replay_corpus_payload(replay_corpus)
    return AssetCheckResult(
        passed=passed,
        metadata={"count": len(replay_corpus)},
    )


@asset_check(asset=eval_report)
def eval_report_check(eval_report: dict) -> AssetCheckResult:
    report_dir = Path(eval_report["report_dir"])
    return AssetCheckResult(
        passed=report_dir.exists() and (report_dir / "run.json").exists(),
        metadata={"report_dir": str(report_dir)},
    )


ALL_ASSETS = [
    gold_datasets,
    replay_corpus,
    replay_results,
    retrieval_metrics,
    workflow_metrics,
    eval_report,
    comparison_report,
]

ALL_ASSET_CHECKS = [
    gold_dataset_check,
    replay_corpus_check,
    eval_report_check,
]

nightly_eval_job = define_asset_job(
    "nightly_eval_job",
    selection=AssetSelection.assets(*ALL_ASSETS),
)

nightly_eval_schedule = ScheduleDefinition(job=nightly_eval_job, cron_schedule="0 2 * * *")


def build_definitions() -> Definitions:
    return Definitions(
        assets=ALL_ASSETS,
        asset_checks=ALL_ASSET_CHECKS,
        jobs=[nightly_eval_job],
        schedules=[nightly_eval_schedule],
    )


def validate_gold_dataset_payload(payload: list[dict]) -> bool:
    ids = [item["case_id"] for item in payload]
    return bool(payload) and len(ids) == len(set(ids))


def validate_replay_corpus_payload(payload: list[dict]) -> bool:
    ids = [item["case_id"] for item in payload]
    has_steps = all(item.get("steps") for item in payload)
    return bool(payload) and len(ids) == len(set(ids)) and has_steps
