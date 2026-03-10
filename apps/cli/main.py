from __future__ import annotations

import argparse
import json
from pathlib import Path

from packages.core.config import (
    agent_tmp_root,
    backups_root,
    ensure_runtime_layout,
    evals_root,
    indexes_root,
    kb_root,
    ledgers_root,
    legacy_repo_runtime_paths,
    observability_root,
    replay_root,
    reports_root,
    sandboxes_root,
    tasks_root,
    validate_runtime_roots,
    worktrees_root,
)
from packages.core.eval import (
    EvaluationRunner,
    build_release_check_report,
    check_contract_drift,
    compare_runs,
    load_eval_thresholds,
    load_gold_cases,
    load_replay_cases,
    resolve_baseline_run_id,
    write_eval_run,
    write_release_check_report,
)
from packages.core.schemas import ComparisonReport
from packages.core.storage.fs_utils import utc_now
from packages.core.storage.recovery import backup_workspace, restore_workspace
from packages.core.stores.ledger_store import LedgerStore


def main() -> int:
    parser = argparse.ArgumentParser(description="agent-foundation unified CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap = subparsers.add_parser("bootstrap-runtime", help="Create state/workspace roots and report legacy repo-local paths")
    bootstrap.set_defaults(func=_cmd_bootstrap_runtime)

    cleanup = subparsers.add_parser("cleanup-runtime", help="Inspect or prune legacy repo-local runtime paths")
    cleanup.add_argument("--remove-empty", action="store_true")
    cleanup.set_defaults(func=_cmd_cleanup_runtime)

    replay = subparsers.add_parser("replay", help="Run the frozen replay corpus")
    replay.add_argument("--eval-root", default=None)
    replay.add_argument("--reports-root", default=None)
    replay.add_argument("--run-id", default=None)
    replay.set_defaults(func=_cmd_replay)

    eval_cmd = subparsers.add_parser("eval", help="Run the frozen eval corpus")
    eval_cmd.add_argument("--eval-root", default=None)
    eval_cmd.add_argument("--reports-root", default=None)
    eval_cmd.add_argument("--run-id", default=None)
    eval_cmd.set_defaults(func=_cmd_eval)

    release = subparsers.add_parser("release-check", help="Run contracts/replay/eval gates and emit a machine-readable report")
    release.add_argument("--eval-root", default=None)
    release.add_argument("--reports-root", default=None)
    release.add_argument("--run-id", default=None)
    release.add_argument("--profile", default="smoke")
    release.set_defaults(func=_cmd_release_check)

    backup = subparsers.add_parser("backup-state", help="Create a backup archive for the full state root")
    backup.add_argument("--output", required=True)
    backup.set_defaults(func=_cmd_backup_state)

    restore = subparsers.add_parser("restore-state", help="Restore a backup archive into the configured state root")
    restore.add_argument("--archive", required=True)
    restore.set_defaults(func=_cmd_restore_state)

    migrate_artifact = subparsers.add_parser("migrate-artifact-schema", help="Emit an artifact schema migration skeleton")
    migrate_artifact.add_argument("--from-version", required=True)
    migrate_artifact.add_argument("--to-version", required=True)
    migrate_artifact.set_defaults(func=_cmd_migrate_artifact_schema)

    migrate_kb = subparsers.add_parser("migrate-thin-kb-schema", help="Emit a thin-KB schema migration skeleton")
    migrate_kb.add_argument("--from-version", required=True)
    migrate_kb.add_argument("--to-version", required=True)
    migrate_kb.set_defaults(func=_cmd_migrate_thin_kb_schema)

    args = parser.parse_args()
    return int(args.func(args))


def _cmd_bootstrap_runtime(args: argparse.Namespace) -> int:
    validate_runtime_roots()
    layout = ensure_runtime_layout()
    payload = {
        "state": {key: str(path) for key, path in layout["state"].items()},
        "workspace": {key: str(path) for key, path in layout["workspace"].items()},
        "legacy_repo_runtime_paths": [str(path) for path in legacy_repo_runtime_paths()],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _cmd_cleanup_runtime(args: argparse.Namespace) -> int:
    validate_runtime_roots()
    cleaned: list[str] = []
    legacy = legacy_repo_runtime_paths()
    if args.remove_empty:
        for path in legacy:
            if path.exists() and path.is_dir() and not any(path.iterdir()):
                path.rmdir()
                cleaned.append(str(path))
    payload = {
        "legacy_repo_runtime_paths": [str(path) for path in legacy],
        "removed": cleaned,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _cmd_replay(args: argparse.Namespace) -> int:
    validate_runtime_roots()
    runner = EvaluationRunner()
    run = runner.run(
        gold_cases=[],
        replay_cases=load_replay_cases(Path(args.eval_root) if args.eval_root else None),
        run_id=args.run_id,
    )
    report_dir = write_eval_run(run, Path(args.reports_root) if args.reports_root else None)
    LedgerStore(ledgers_root()).append_replay_run_event(
        run.run_id,
        "replay_run_completed",
        actor="cli",
        run_id=run.run_id,
        cases_total=len(run.replay_results),
        ok=all(item.ok for item in run.replay_results),
        report_dir=str(report_dir),
    )
    print(report_dir)
    return 0 if all(item.ok for item in run.replay_results) else 1


def _cmd_eval(args: argparse.Namespace) -> int:
    validate_runtime_roots()
    runner = EvaluationRunner()
    run = runner.run(
        gold_cases=load_gold_cases(Path(args.eval_root) if args.eval_root else None),
        replay_cases=load_replay_cases(Path(args.eval_root) if args.eval_root else None),
        run_id=args.run_id,
    )
    report_dir = write_eval_run(run, Path(args.reports_root) if args.reports_root else None)
    LedgerStore(ledgers_root()).append_replay_run_event(
        run.run_id,
        "eval_run_completed",
        actor="cli",
        run_id=run.run_id,
        gold_cases=len(run.retrieval_results),
        replay_cases=len(run.replay_results),
        report_dir=str(report_dir),
    )
    print(report_dir)
    return 0


def _cmd_release_check(args: argparse.Namespace) -> int:
    validate_runtime_roots()
    eval_root = Path(args.eval_root) if args.eval_root else evals_root()
    report_root = Path(args.reports_root) if args.reports_root else reports_root()
    profile = args.profile
    started_at = utc_now().isoformat()
    runner = EvaluationRunner()
    run = runner.run(
        gold_cases=load_gold_cases(eval_root),
        replay_cases=load_replay_cases(eval_root),
        run_id=args.run_id,
    )
    eval_report_dir = write_eval_run(run, report_root)
    thresholds = load_eval_thresholds(eval_root, profile=profile)
    baseline_run_id = resolve_baseline_run_id(eval_root)
    comparison: ComparisonReport | None = None
    if baseline_run_id:
        baseline_dir = report_root / "eval" / baseline_run_id
        if baseline_dir.exists():
            comparison = compare_runs(
                baseline_dir,
                eval_report_dir,
                eval_report_dir / "comparison.json",
            )
        else:
            comparison = ComparisonReport(
                baseline_run_id=baseline_run_id,
                candidate_run_id=run.run_id,
                metric_deltas={},
                regressed_case_ids=[],
                new_critical_failures=[],
                threshold_failures=[],
                baseline_missing=True,
                overall_status="no_baseline",
            )
    elif thresholds.require_baseline:
        comparison = ComparisonReport(
            baseline_run_id="",
            candidate_run_id=run.run_id,
            metric_deltas={},
            regressed_case_ids=[],
            new_critical_failures=[],
            threshold_failures=[],
            baseline_missing=True,
            overall_status="no_baseline",
        )

    report = build_release_check_report(
        run=run,
        profile=profile,
        contract_drift=check_contract_drift(),
        comparison=comparison,
        thresholds=thresholds,
        started_at=started_at,
        ended_at=utc_now().isoformat(),
        report_root=report_root,
    )
    release_dir = write_release_check_report(report, report_root)
    ledger = LedgerStore(ledgers_root())
    ledger.append_replay_run_event(
        run.run_id,
        "release_check_eval_completed",
        actor="cli",
        run_id=run.run_id,
        profile=profile,
        report_dir=str(eval_report_dir),
    )
    ledger.append_release_event(
        run.run_id,
        "release_check_completed",
        actor="cli",
        run_id=run.run_id,
        profile=profile,
        contract_drift=report.contract_drift,
        replay_ok=report.replay_ok,
        eval_ok=report.eval_ok,
        overall_status=report.overall_status,
        release_check_dir=str(release_dir),
    )
    print(release_dir)
    return 0 if report.overall_status == "ok" else 1


def _cmd_backup_state(args: argparse.Namespace) -> int:
    validate_runtime_roots()
    archive = Path(args.output)
    result = backup_workspace(
        tasks_root=tasks_root(),
        kb_root=kb_root(),
        indexes_root=indexes_root(),
        ledgers_root=ledgers_root(),
        replay_root=replay_root(),
        backups_root=backups_root(),
        observability_root=observability_root(),
        output_path=archive,
    )
    LedgerStore(ledgers_root()).append_release_event(
        archive.stem,
        "backup_completed",
        actor="cli",
        archive_path=str(archive.resolve()),
        sections=result["sections"],
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _cmd_restore_state(args: argparse.Namespace) -> int:
    validate_runtime_roots()
    result = restore_workspace(
        archive_path=Path(args.archive),
        tasks_root=tasks_root(),
        kb_root=kb_root(),
        indexes_root=indexes_root(),
        ledgers_root=ledgers_root(),
        replay_root=replay_root(),
        observability_root=observability_root(),
    )
    LedgerStore(ledgers_root()).append_release_event(
        Path(args.archive).stem,
        "restore_completed",
        actor="cli",
        archive_path=str(Path(args.archive).resolve()),
        tasks_root=str(tasks_root()),
        kb_root=str(kb_root()),
        indexes_root=str(indexes_root()),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _cmd_migrate_artifact_schema(args: argparse.Namespace) -> int:
    payload = {
        "migration_type": "artifact_schema",
        "from_version": args.from_version,
        "to_version": args.to_version,
        "command_template": "python -m apps.cli.main migrate-artifact-schema --from-version X --to-version Y",
        "suggested_workdirs": [str(tasks_root()), str(worktrees_root()), str(agent_tmp_root())],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _cmd_migrate_thin_kb_schema(args: argparse.Namespace) -> int:
    payload = {
        "migration_type": "thin_kb_schema",
        "from_version": args.from_version,
        "to_version": args.to_version,
        "command_template": "python -m apps.cli.main migrate-thin-kb-schema --from-version X --to-version Y",
        "suggested_workdirs": [str(kb_root()), str(sandboxes_root())],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
