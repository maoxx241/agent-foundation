from __future__ import annotations

import argparse
from pathlib import Path

from packages.core.config import reports_root
from packages.core.eval import EvaluationRunner, load_gold_cases, load_shadow_manifest
from packages.core.eval.reporting import new_run_id, write_eval_run
from packages.core.eval.shadow import summarize_shadow_run, write_shadow_checklist, write_shadow_summary
from packages.core.schemas import ReplayCase
from packages.core.storage.fs_utils import ensure_dir, utc_now


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a shadow-mode pilot manifest.")
    parser.add_argument("--manifest", default="evals/corpora/shadow/pilot_manifest.json")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--reports-root", default=None)
    args = parser.parse_args()

    run_id = args.run_id or new_run_id("shadow")
    started_at = utc_now().isoformat()
    manifest = load_shadow_manifest(Path(args.manifest))
    replay_cases = [_shadow_safe_case(case) for case in manifest.cases]
    runner = EvaluationRunner()
    run = runner.run(gold_cases=load_gold_cases(), replay_cases=replay_cases, run_id=run_id)
    report_root = Path(args.reports_root) if args.reports_root else reports_root()
    write_eval_run(run, report_root)

    shadow_dir = report_root / "shadow" / run_id
    ensure_dir(shadow_dir)
    summary = summarize_shadow_run(
        run_id=run_id,
        started_at=started_at,
        ended_at=utc_now().isoformat(),
        shadow_report_dir=shadow_dir,
        eval_run=run,
    )
    write_shadow_summary(summary, shadow_dir / "run-summary.json")
    write_shadow_checklist(summary, shadow_dir / "shadow-checklist.md")
    print(shadow_dir)
    return 0


def _shadow_safe_case(case: ReplayCase) -> ReplayCase:
    payload = case.model_dump(mode="json", by_alias=True)
    for step in payload.get("steps", []):
        if step.get("path") == "/v1/kb/writeback/refine":
            step.setdefault("json", {})
            step["json"]["persist"] = False
    return ReplayCase.model_validate(payload)


if __name__ == "__main__":
    raise SystemExit(main())
