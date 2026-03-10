from __future__ import annotations

import argparse
import json
from pathlib import Path

from packages.core.config import backups_root, indexes_root, kb_root, ledgers_root, observability_root, replay_root, tasks_root
from packages.core.storage.recovery import backup_workspace


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a backup archive for the state root")
    parser.add_argument("--tasks-root", type=Path, default=tasks_root())
    parser.add_argument("--kb-root", type=Path, default=kb_root())
    parser.add_argument("--indexes-root", type=Path, default=indexes_root())
    parser.add_argument("--ledgers-root", type=Path, default=ledgers_root())
    parser.add_argument("--replay-root", type=Path, default=replay_root())
    parser.add_argument("--backups-root", type=Path, default=backups_root())
    parser.add_argument("--observability-root", type=Path, default=observability_root())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = backup_workspace(
        tasks_root=args.tasks_root,
        kb_root=args.kb_root,
        indexes_root=args.indexes_root if args.indexes_root.exists() else None,
        ledgers_root=args.ledgers_root if args.ledgers_root.exists() else None,
        replay_root=args.replay_root if args.replay_root.exists() else None,
        backups_root=args.backups_root if args.backups_root.exists() else None,
        observability_root=args.observability_root if args.observability_root.exists() else None,
        output_path=args.output,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
