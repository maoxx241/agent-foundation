from __future__ import annotations

import argparse
from pathlib import Path

from packages.core.eval import EvaluationRunner, load_gold_cases, load_replay_cases, write_eval_run
from packages.core.eval.reporting import new_run_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Run frozen evaluation corpora and write a report.")
    parser.add_argument("--eval-root", default=None)
    parser.add_argument("--reports-root", default=None)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    runner = EvaluationRunner()
    run = runner.run(
        gold_cases=load_gold_cases(Path(args.eval_root) if args.eval_root else None),
        replay_cases=load_replay_cases(Path(args.eval_root) if args.eval_root else None),
        run_id=args.run_id or new_run_id(),
    )
    report_dir = write_eval_run(run, Path(args.reports_root) if args.reports_root else None)
    print(report_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
