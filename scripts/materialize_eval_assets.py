from __future__ import annotations

import argparse
import os

from dagster import materialize

from packages.core.pipeline.dagster_defs import ALL_ASSETS


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize eval Dagster assets.")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--eval-root", default=None)
    parser.add_argument("--reports-root", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--baseline-run-id", default=None)
    args = parser.parse_args()

    _set_env("AGENT_FOUNDATION_REPO_ROOT", args.repo_root)
    _set_env("AGENT_FOUNDATION_EVALS_ROOT", args.eval_root)
    _set_env("AGENT_FOUNDATION_REPORTS_ROOT", args.reports_root)
    _set_env("AGENT_FOUNDATION_RUN_ID", args.run_id)
    _set_env("AGENT_FOUNDATION_BASELINE_RUN_ID", args.baseline_run_id)

    result = materialize(ALL_ASSETS)
    return 0 if result.success else 1


def _set_env(name: str, value: str | None) -> None:
    if value:
        os.environ[name] = value


if __name__ == "__main__":
    raise SystemExit(main())
