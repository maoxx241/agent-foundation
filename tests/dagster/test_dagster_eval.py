from __future__ import annotations

import shutil
from pathlib import Path

from dagster import materialize

from packages.core.pipeline.dagster_defs import (
    ALL_ASSET_CHECKS,
    ALL_ASSETS,
    build_definitions,
    eval_report,
    gold_datasets,
    nightly_eval_schedule,
    replay_corpus,
    replay_results,
    retrieval_metrics,
    validate_gold_dataset_payload,
    validate_replay_corpus_payload,
    workflow_metrics,
)
from packages.core.eval import load_gold_cases, load_replay_cases


def test_dagster_materializes_reports(tmp_path, monkeypatch):
    repo_root = _copy_eval_root(tmp_path)
    monkeypatch.setenv("AGENT_FOUNDATION_REPO_ROOT", str(repo_root))
    monkeypatch.setenv("AGENT_FOUNDATION_EVALS_ROOT", str(repo_root / "evals"))
    monkeypatch.setenv("AGENT_FOUNDATION_REPORTS_ROOT", str(repo_root / "generated" / "reports"))
    monkeypatch.setenv("AGENT_FOUNDATION_RUN_ID", "dagster-test")

    result = materialize(ALL_ASSETS)
    assert result.success
    assert (repo_root / "generated" / "reports" / "eval" / "dagster-test" / "run.json").exists()


def test_dagster_partial_subset_materializes_dependencies(tmp_path, monkeypatch):
    repo_root = _copy_eval_root(tmp_path)
    monkeypatch.setenv("AGENT_FOUNDATION_REPO_ROOT", str(repo_root))
    monkeypatch.setenv("AGENT_FOUNDATION_EVALS_ROOT", str(repo_root / "evals"))
    monkeypatch.setenv("AGENT_FOUNDATION_REPORTS_ROOT", str(repo_root / "generated" / "reports"))
    monkeypatch.setenv("AGENT_FOUNDATION_RUN_ID", "dagster-partial")

    result = materialize([gold_datasets, replay_corpus, replay_results, retrieval_metrics, workflow_metrics, eval_report])
    assert result.success


def test_dagster_materializes_without_repo_local_shadow_runs(tmp_path, monkeypatch):
    repo_root = _copy_eval_root(tmp_path)
    state_root = tmp_path / "state"
    monkeypatch.setenv("AGENT_FOUNDATION_REPO_ROOT", str(repo_root))
    monkeypatch.setenv("AGENT_FOUNDATION_STATE_ROOT", str(state_root))
    monkeypatch.setenv("AGENT_FOUNDATION_EVALS_ROOT", str(repo_root / "evals"))
    monkeypatch.setenv("AGENT_FOUNDATION_REPORTS_ROOT", str(repo_root / "generated" / "reports"))
    monkeypatch.setenv("AGENT_FOUNDATION_RUN_ID", "dagster-shadow-lock")

    result = materialize(ALL_ASSETS)

    assert result.success
    assert (repo_root / "generated" / "reports" / "eval" / "dagster-shadow-lock" / "run.json").exists()
    assert (state_root / "replay" / "captured_runs" / "dagster-shadow-lock").exists()
    assert not (repo_root / "shadow_runs").exists()


def test_dagster_invalid_replay_input_blocks_downstream(tmp_path, monkeypatch):
    repo_root = _copy_eval_root(tmp_path)
    (repo_root / "evals" / "corpora" / "replay" / "smoke.jsonl").write_text('{"case_id":"broken"}\n', encoding="utf-8")
    monkeypatch.setenv("AGENT_FOUNDATION_REPO_ROOT", str(repo_root))
    monkeypatch.setenv("AGENT_FOUNDATION_EVALS_ROOT", str(repo_root / "evals"))
    monkeypatch.setenv("AGENT_FOUNDATION_REPORTS_ROOT", str(repo_root / "generated" / "reports"))
    monkeypatch.setenv("AGENT_FOUNDATION_RUN_ID", "dagster-bad")

    result = materialize(ALL_ASSETS, raise_on_error=False)
    assert result.success is False
    assert not (repo_root / "generated" / "reports" / "eval" / "dagster-bad" / "run.json").exists()


def test_dagster_graph_checks_retry_and_schedule_metadata():
    defs = build_definitions()
    graph = defs.get_repository_def().asset_graph

    assert "replay_results" in {key.to_user_string() for key in graph.materializable_asset_keys}
    assert {key.to_user_string() for key in graph.get(eval_report.key).parent_keys} == {
        "replay_results",
        "retrieval_metrics",
        "workflow_metrics",
    }
    assert all(asset.op.retry_policy is not None for asset in [gold_datasets, replay_corpus, replay_results])
    assert len(ALL_ASSET_CHECKS) == 3
    assert nightly_eval_schedule.cron_schedule == "0 2 * * *"
    assert validate_gold_dataset_payload([item.model_dump(mode="json") for item in load_gold_cases()])
    assert validate_replay_corpus_payload([item.model_dump(mode="json") for item in load_replay_cases()])


def _copy_eval_root(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    target_root = tmp_path / "repo"
    shutil.copytree(repo_root / "evals", target_root / "evals")
    return target_root
