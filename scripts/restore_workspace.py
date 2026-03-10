from __future__ import annotations

import argparse
import json
from pathlib import Path

from packages.core.config import backups_root, indexes_root, ledgers_root, observability_root, replay_root
from packages.core.storage.recovery import restore_workspace


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore a backup archive into the state root")
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--tasks-root", type=Path, required=True)
    parser.add_argument("--kb-root", type=Path, required=True)
    parser.add_argument("--indexes-root", type=Path, default=indexes_root())
    parser.add_argument("--ledgers-root", type=Path, default=ledgers_root())
    parser.add_argument("--replay-root", type=Path, default=replay_root())
    parser.add_argument("--backups-root", type=Path, default=backups_root())
    parser.add_argument("--observability-root", type=Path, default=observability_root())
    args = parser.parse_args()

    result = restore_workspace(
        archive_path=args.archive,
        tasks_root=args.tasks_root,
        kb_root=args.kb_root,
        indexes_root=args.indexes_root,
        ledgers_root=args.ledgers_root,
        replay_root=args.replay_root,
        backups_root=args.backups_root,
        observability_root=args.observability_root,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
