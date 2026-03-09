from __future__ import annotations

import argparse
import json
from pathlib import Path

from libs.storage.recovery import restore_workspace


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore a backup archive into tasks/, kb/, and observability/")
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--tasks-root", type=Path, required=True)
    parser.add_argument("--kb-root", type=Path, required=True)
    parser.add_argument("--observability-root", type=Path)
    args = parser.parse_args()

    result = restore_workspace(
        archive_path=args.archive,
        tasks_root=args.tasks_root,
        kb_root=args.kb_root,
        observability_root=args.observability_root,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
