from __future__ import annotations

import json
from pathlib import Path

from packages.core.config import reports_root
from packages.core.schemas import ComparisonReport, EvalRun
from packages.core.storage.fs_utils import ensure_dir, utc_now, write_json_atomic, write_text_atomic
from .metrics import compare_metric_maps


def default_reports_root() -> Path:
    return reports_root()


def write_eval_run(run: EvalRun, reports_root: Path | None = None) -> Path:
    reports_root = reports_root or default_reports_root()
    report_dir = reports_root / "eval" / run.run_id
    ensure_dir(report_dir)
    payload = run.model_dump(mode="json")
    payload["report_dir"] = str(report_dir)
    write_json_atomic(report_dir / "run.json", payload)
    write_json_atomic(report_dir / "retrieval-results.json", [item.model_dump(mode="json") for item in run.retrieval_results])
    write_json_atomic(report_dir / "replay-results.json", [item.model_dump(mode="json") for item in run.replay_results])
    write_text_atomic(report_dir / "report.md", write_markdown_report(EvalRun.model_validate(payload)))
    return report_dir


def write_markdown_report(run: EvalRun) -> str:
    retrieval = run.retrieval_metrics.model_dump(mode="json")
    workflow = run.workflow_metrics.model_dump(mode="json")
    return (
        f"# Eval Report {run.run_id}\n\n"
        f"Generated at: {run.generated_at}\n\n"
        "## Retrieval Metrics\n\n"
        f"{json.dumps(retrieval, indent=2, sort_keys=True)}\n\n"
        "## Workflow Metrics\n\n"
        f"{json.dumps(workflow, indent=2, sort_keys=True)}\n"
    )


def compare_runs(
    baseline_dir: Path,
    candidate_dir: Path,
    output_path: Path | None = None,
) -> ComparisonReport:
    baseline = EvalRun.model_validate(json.loads((baseline_dir / "run.json").read_text(encoding="utf-8")))
    candidate = EvalRun.model_validate(json.loads((candidate_dir / "run.json").read_text(encoding="utf-8")))
    retrieval = compare_metric_maps(
        baseline.retrieval_metrics.model_dump(mode="json"),
        candidate.retrieval_metrics.model_dump(mode="json"),
    )
    workflow = compare_metric_maps(
        baseline.workflow_metrics.model_dump(mode="json"),
        candidate.workflow_metrics.model_dump(mode="json"),
    )

    shadow_root = baseline_dir.parents[1] / "shadow"
    baseline_shadow = _load_shadow_summary(shadow_root / baseline.run_id / "run-summary.json")
    candidate_shadow = _load_shadow_summary(shadow_root / candidate.run_id / "run-summary.json")
    new_critical_failures = sorted(
        set(candidate_shadow.get("critical_boundary_failures", [])) - set(baseline_shadow.get("critical_boundary_failures", []))
    )
    regressed_case_ids = sorted(set(retrieval.regressed_case_ids + workflow.regressed_case_ids + _regressed_case_ids(baseline, candidate)))
    report = ComparisonReport(
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        metric_deltas={**retrieval.metric_deltas, **workflow.metric_deltas},
        regressed_case_ids=regressed_case_ids,
        new_critical_failures=new_critical_failures,
        overall_status=(
            "regression"
            if regressed_case_ids
            or new_critical_failures
            or retrieval.overall_status == "regression"
            or workflow.overall_status == "regression"
            else "ok"
        ),
    )
    if output_path is not None:
        write_json_atomic(output_path, report.model_dump(mode="json"))
    return report


def new_run_id(label: str = "eval") -> str:
    timestamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{label}"


def _regressed_case_ids(baseline: EvalRun, candidate: EvalRun) -> list[str]:
    baseline_success = {item.case_id: item.ok for item in baseline.replay_results}
    baseline_hits = {item.case_id: bool(set(item.expected_ids) & set(item.actual_ids[:5])) for item in baseline.retrieval_results}
    regressed: list[str] = []
    for item in candidate.replay_results:
        if baseline_success.get(item.case_id, False) and not item.ok:
            regressed.append(item.case_id)
    for item in candidate.retrieval_results:
        if baseline_hits.get(item.case_id, False) and not bool(set(item.expected_ids) & set(item.actual_ids[:5])):
            regressed.append(item.case_id)
    return sorted(set(regressed))


def _load_shadow_summary(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
