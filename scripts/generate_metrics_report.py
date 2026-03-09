from __future__ import annotations

import argparse
import json
from pathlib import Path

from libs.observability import build_metrics_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate observability events and metrics into one report")
    parser.add_argument("--observability-root", type=Path, default=Path("observability"))
    args = parser.parse_args()

    report = build_metrics_report(args.observability_root)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
