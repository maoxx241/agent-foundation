from __future__ import annotations

import argparse
import json
from pathlib import Path

from packages.core.config import kb_root, observability_root, tasks_root
from packages.core.storage.recovery import backup_workspace


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a backup archive for tasks/, kb/, and observability/")
    parser.add_argument("--tasks-root", type=Path, default=tasks_root())
    parser.add_argument("--kb-root", type=Path, default=kb_root())
    parser.add_argument("--observability-root", type=Path, default=observability_root())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = backup_workspace(
        tasks_root=args.tasks_root,
        kb_root=args.kb_root,
        observability_root=args.observability_root if args.observability_root.exists() else None,
        output_path=args.output,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
