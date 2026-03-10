from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from packages.core.observability import Observability
from packages.core.schemas import EvalRun, InterventionRecord, RunSummary
from packages.core.storage.fs_utils import ensure_dir, utc_now, write_json_atomic, write_text_atomic
from .metrics import compute_workflow_metrics


def append_intervention(report_root: Path, record: InterventionRecord, observability_root: Path | None = None) -> Path:
    ensure_dir(report_root)
    path = report_root / "interventions.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(record.model_dump_json() + "\n")
    if observability_root is not None:
        observability = Observability(observability_root)
        observability.emit_event(
            "human_intervention",
            run_id=record.run_id,
            task_id=record.task_id,
            stage=record.stage,
            issue_type=record.issue_type,
            severity=record.severity,
            fix_type=record.fix_type,
            missing_plane=record.missing_plane,
            resolved=record.resolved,
        )
    return path


def summarize_shadow_run(
    *,
    run_id: str,
    started_at: str,
    ended_at: str | None,
    shadow_report_dir: Path,
    eval_run: EvalRun,
) -> RunSummary:
    interventions = list(_load_interventions(shadow_report_dir / "interventions.jsonl"))
    terminal_counter: Counter[str] = Counter()
    promoted_total = 0
    failure_modes: Counter[str] = Counter()
    critical_failures: list[str] = []

    for result in eval_run.replay_results:
        for state in result.final_states.values():
            terminal_counter[state] += 1
        for step in result.steps:
            promoted_total += step.promoted_object_count
            if step.status_code >= 400 and "/v1/tasks/" in step.path:
                failure_modes["artifact_api_error"] += 1
            if step.status_code >= 400 and "/v1/kb/" in step.path:
                failure_modes["thin_kb_api_error"] += 1
            if step.status_code >= 500:
                critical_failures.append(f"{result.case_id}:{step.path}")

    for item in interventions:
        failure_modes[item.issue_type] += 1

    workflow_metrics = compute_workflow_metrics(
        eval_run.replay_results,
        intervention_task_ids={item.task_id for item in interventions},
        regression_escape_task_ids={item.task_id for item in interventions if item.issue_type == "regression_escape"},
    )

    return RunSummary(
        run_id=run_id,
        started_at=started_at,
        ended_at=ended_at or utc_now().isoformat(),
        tasks_total=len({task_id for result in eval_run.replay_results for task_id in result.task_ids}),
        task_terminal_states=dict(sorted(terminal_counter.items())),
        retrieval_metrics=eval_run.retrieval_metrics.model_dump(mode="json"),
        workflow_metrics=workflow_metrics.model_dump(mode="json"),
        interventions_total=len(interventions),
        promoted_objects_total=promoted_total,
        critical_boundary_failures=sorted(set(critical_failures)),
        top_failure_modes=[name for name, _ in failure_modes.most_common(5)],
    )


def write_shadow_checklist(summary: RunSummary, output_path: Path) -> None:
    checklist = [
        f"# Shadow Checklist {summary.run_id}",
        "",
        f"- Tasks reviewed: {summary.tasks_total}",
        f"- Interventions logged: {summary.interventions_total}",
        f"- Promoted objects: {summary.promoted_objects_total}",
        f"- Critical boundary failures: {len(summary.critical_boundary_failures)}",
        f"- Top failure modes: {', '.join(summary.top_failure_modes) if summary.top_failure_modes else 'none'}",
    ]
    write_text_atomic(output_path, "\n".join(checklist) + "\n")


def write_shadow_summary(summary: RunSummary, output_path: Path) -> None:
    write_json_atomic(output_path, summary.model_dump(mode="json"))


def _load_interventions(path: Path) -> list[InterventionRecord]:
    if not path.exists():
        return []
    items: list[InterventionRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        items.append(InterventionRecord.model_validate(json.loads(line)))
    return items
