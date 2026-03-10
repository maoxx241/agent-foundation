from __future__ import annotations

import argparse
import json
from pathlib import Path

from packages.core.config import kb_root
from packages.core.storage.recovery import detect_manifest_mismatch


def main() -> None:
    parser = argparse.ArgumentParser(description="Check for Thin KB canonical/manifest mismatch")
    parser.add_argument("--kb-root", type=Path, default=kb_root())
    parser.add_argument("--db-path", type=Path)
    args = parser.parse_args()

    result = detect_manifest_mismatch(
        kb_root=args.kb_root,
        db_path=args.db_path or (args.kb_root / "manifest.sqlite3"),
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
