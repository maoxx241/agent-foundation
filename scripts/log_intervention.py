from __future__ import annotations

import argparse
from pathlib import Path

from libs.eval.shadow import append_intervention
from libs.schemas import InterventionRecord
from libs.storage.fs_utils import utc_now


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a shadow-mode intervention record.")
    parser.add_argument("run_id")
    parser.add_argument("task_id")
    parser.add_argument("stage")
    parser.add_argument("issue_type")
    parser.add_argument("severity")
    parser.add_argument("fix_type")
    parser.add_argument("--missing-plane", default="none")
    parser.add_argument("--notes", default=None)
    parser.add_argument("--resolved", action="store_true")
    parser.add_argument("--reports-root", default="reports")
    parser.add_argument("--observability-root", default=None)
    args = parser.parse_args()

    record = InterventionRecord(
        run_id=args.run_id,
        task_id=args.task_id,
        stage=args.stage,
        issue_type=args.issue_type,
        severity=args.severity,
        fix_type=args.fix_type,
        missing_plane=args.missing_plane,
        notes=args.notes,
        timestamp=utc_now().isoformat(),
        resolved=args.resolved,
    )
    path = append_intervention(
        Path(args.reports_root) / "shadow" / args.run_id,
        record,
        Path(args.observability_root) if args.observability_root else None,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
