from __future__ import annotations

import json

from packages.core.eval import EvaluationRunner, compare_runs, load_gold_cases, load_replay_cases, write_eval_run
from packages.core.schemas import EvalRun, ReplayCaseResult, RetrievalCaseResult


def test_eval_runner_writes_reports_from_frozen_corpora(tmp_path):
    runner = EvaluationRunner(repo_root=tmp_path, workspace_root=tmp_path / "shadow_runs")
    run = runner.run(
        gold_cases=load_gold_cases()[:2],
        replay_cases=load_replay_cases()[:2],
        run_id="eval-runner-test",
    )
    report_dir = write_eval_run(run, tmp_path / "reports")

    assert report_dir.exists()
    payload = json.loads((report_dir / "run.json").read_text(encoding="utf-8"))
    assert payload["run_id"] == "eval-runner-test"
    assert payload["retrieval_results"]
    assert payload["replay_results"]
    replay_payload = json.loads((tmp_path / "reports" / "replay" / "eval-runner-test" / "run.json").read_text(encoding="utf-8"))
    assert replay_payload["run_id"] == "eval-runner-test"
    assert replay_payload["ok"] is True


def test_eval_runner_repo_root_does_not_force_repo_local_shadow_runs(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    shadow_root = tmp_path / "state" / "replay" / "captured_runs"
    repo_root.mkdir()
    monkeypatch.setenv("AGENT_FOUNDATION_REPO_ROOT", str(repo_root))
    monkeypatch.setenv("AGENT_FOUNDATION_SHADOW_RUNS_ROOT", str(shadow_root))

    runner = EvaluationRunner(repo_root=repo_root)

    assert runner.repo_root == repo_root.resolve()
    assert runner.workspace_root == shadow_root.resolve()
    assert runner.workspace_root != (repo_root / "shadow_runs").resolve()
    assert not (repo_root / "shadow_runs").exists()


def test_compare_runs_flags_regressed_case_ids(tmp_path):
    baseline = EvalRun(
        run_id="baseline",
        generated_at="2026-03-09T00:00:00+00:00",
        retrieval_results=[RetrievalCaseResult(case_id="gold-1", expected_ids=["claim-a"], actual_ids=["claim-a"])],
        replay_results=[ReplayCaseResult(case_id="replay-1", kind="workflow", task_ids=["task-a"], ok=True)],
    )
    candidate = EvalRun(
        run_id="candidate",
        generated_at="2026-03-09T00:00:00+00:00",
        retrieval_results=[RetrievalCaseResult(case_id="gold-1", expected_ids=["claim-a"], actual_ids=[])],
        replay_results=[ReplayCaseResult(case_id="replay-1", kind="workflow", task_ids=["task-a"], ok=False)],
    )

    baseline_dir = write_eval_run(baseline, tmp_path / "reports")
    candidate_dir = write_eval_run(candidate, tmp_path / "reports")
    shadow_root = tmp_path / "reports" / "shadow"
    (shadow_root / "baseline").mkdir(parents=True)
    (shadow_root / "candidate").mkdir(parents=True)
    (shadow_root / "baseline" / "run-summary.json").write_text('{"critical_boundary_failures":[]}\n', encoding="utf-8")
    (shadow_root / "candidate" / "run-summary.json").write_text(
        '{"critical_boundary_failures":["candidate:/v1/kb/search/hybrid"]}\n',
        encoding="utf-8",
    )
    report = compare_runs(baseline_dir, candidate_dir)

    assert report.overall_status == "regression"
    assert set(report.regressed_case_ids) == {"gold-1", "replay-1"}
    assert report.new_critical_failures == ["candidate:/v1/kb/search/hybrid"]
