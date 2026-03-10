from __future__ import annotations

import argparse
from pathlib import Path

from packages.core.config import reports_root
from packages.core.eval import compare_runs


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two stored evaluation runs.")
    parser.add_argument("baseline_run")
    parser.add_argument("candidate_run")
    parser.add_argument("--reports-root", default=None)
    args = parser.parse_args()

    report_root = Path(args.reports_root) if args.reports_root else reports_root()
    report = compare_runs(
        report_root / "eval" / args.baseline_run,
        report_root / "eval" / args.candidate_run,
        report_root / "eval" / args.candidate_run / "comparison.json",
    )
    print(report.model_dump_json(indent=2))
    return 0 if report.overall_status != "regression" else 1


if __name__ == "__main__":
    raise SystemExit(main())
