from __future__ import annotations

import json

from packages.core.eval.shadow import append_intervention, summarize_shadow_run, write_shadow_checklist, write_shadow_summary
from packages.core.schemas import EvalRun, InterventionRecord, ReplayCaseResult, ReplayStepResult, RetrievalMetrics, WorkflowMetrics


def test_shadow_summary_uses_logged_interventions(tmp_path):
    shadow_dir = tmp_path / "reports" / "shadow" / "run-1"
    append_intervention(
        shadow_dir,
        InterventionRecord(
            run_id="run-1",
            task_id="task-1",
            stage="60_validation",
            issue_type="regression_escape",
            severity="high",
            fix_type="manual_patch",
            missing_plane="artifact",
            timestamp="2026-03-09T00:00:00+00:00",
            resolved=True,
        ),
    )

    eval_run = EvalRun(
        run_id="run-1",
        generated_at="2026-03-09T00:00:00+00:00",
        replay_results=[
            ReplayCaseResult(
                case_id="case-1",
                kind="workflow",
                task_ids=["task-1"],
                ok=True,
                final_states={"task-1": "WRITTEN_BACK"},
                steps=[ReplayStepResult(method="POST", path="/v1/kb/writeback/refine", status_code=200, ok=True, promoted_object_count=1)],
            )
        ],
        retrieval_metrics=RetrievalMetrics(hit_at_1=1.0),
        workflow_metrics=WorkflowMetrics(),
    )

    summary = summarize_shadow_run(
        run_id="run-1",
        started_at="2026-03-09T00:00:00+00:00",
        ended_at="2026-03-09T01:00:00+00:00",
        shadow_report_dir=shadow_dir,
        eval_run=eval_run,
    )
    write_shadow_summary(summary, shadow_dir / "run-summary.json")
    write_shadow_checklist(summary, shadow_dir / "shadow-checklist.md")

    saved = json.loads((shadow_dir / "run-summary.json").read_text(encoding="utf-8"))
    assert saved["interventions_total"] == 1
    assert saved["workflow_metrics"]["human_intervention_rate"] == 1.0
    assert saved["workflow_metrics"]["regression_escape_rate"] == 1.0
    assert (shadow_dir / "shadow-checklist.md").exists()
