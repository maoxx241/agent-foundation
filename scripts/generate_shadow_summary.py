from __future__ import annotations

import argparse
import json
from pathlib import Path

from libs.eval.shadow import summarize_shadow_run, write_shadow_checklist, write_shadow_summary
from libs.schemas import EvalRun
from libs.storage.fs_utils import ensure_dir, utc_now


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate shadow summary/checklist from a stored eval run.")
    parser.add_argument("run_id")
    parser.add_argument("--reports-root", default="reports")
    parser.add_argument("--started-at", default=None)
    parser.add_argument("--ended-at", default=None)
    args = parser.parse_args()

    reports_root = Path(args.reports_root)
    eval_run = EvalRun.model_validate(json.loads((reports_root / "eval" / args.run_id / "run.json").read_text(encoding="utf-8")))
    shadow_dir = reports_root / "shadow" / args.run_id
    ensure_dir(shadow_dir)
    summary = summarize_shadow_run(
        run_id=args.run_id,
        started_at=args.started_at or utc_now().isoformat(),
        ended_at=args.ended_at or utc_now().isoformat(),
        shadow_report_dir=shadow_dir,
        eval_run=eval_run,
    )
    write_shadow_summary(summary, shadow_dir / "run-summary.json")
    write_shadow_checklist(summary, shadow_dir / "shadow-checklist.md")
    print(shadow_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
