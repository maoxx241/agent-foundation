from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.core.config import (
    ensure_state_layout,
    kb_root,
    observability_root,
    replay_root,
    repo_root,
    shadow_runs_root,
    sqlite_indexes_root,
    tasks_root,
    validate_runtime_roots,
)
from packages.core.storage.fs_utils import ensure_dir


def main() -> None:
    validate_runtime_roots()
    layout = ensure_state_layout()
    repo = repo_root()

    migrated: list[dict[str, str]] = []
    migrated.extend(_migrate_tasks(repo / "tasks", tasks_root()))
    migrated.extend(_migrate_kb(repo / "kb", kb_root(), sqlite_indexes_root() / "manifest.sqlite3"))
    migrated.extend(_move_tree(repo / "observability", observability_root(), label="observability"))
    migrated.extend(_move_tree(repo / "shadow_runs", shadow_runs_root(), label="shadow_runs"))

    print(
        json.dumps(
            {
                "state_root": str(layout["state_root"]),
                "migrated": migrated,
            },
            indent=2,
            sort_keys=True,
        )
    )


def _migrate_tasks(source: Path, destination: Path) -> list[dict[str, str]]:
    if not source.exists():
        return []
    ensure_dir(destination)
    active_root = destination / "active"
    archived_root = destination / "archived"
    ensure_dir(active_root)
    ensure_dir(archived_root)
    moved: list[dict[str, str]] = []
    if (source / "active").exists() or (source / "archived").exists():
        moved.extend(_move_tree(source / "active", active_root, label="tasks.active"))
        moved.extend(_move_tree(source / "archived", archived_root, label="tasks.archived"))
        if source.exists() and not any(source.iterdir()):
            source.rmdir()
        return moved

    for entry in sorted(source.iterdir()):
        target = active_root / entry.name
        _move_entry(entry, target)
        moved.append({"label": "tasks.active", "from": str(entry), "to": str(target)})
    if source.exists() and not any(source.iterdir()):
        source.rmdir()
    return moved


def _migrate_kb(source: Path, destination: Path, manifest_destination: Path) -> list[dict[str, str]]:
    if not source.exists():
        return []
    ensure_dir(destination)
    moved: list[dict[str, str]] = []

    tier_map = {
        "canonical": destination / "canonical",
        "candidates": destination / "candidates",
        "deprecated": destination / "deprecated",
    }
    for path in tier_map.values():
        ensure_dir(path)

    if any((source / name).exists() for name in tier_map):
        for name, target in tier_map.items():
            moved.extend(_move_tree(source / name, target, label=f"kb.{name}"))
    else:
        moved.extend(_move_object_dirs(source, tier_map["canonical"], label="kb.canonical"))

    for legacy_name in ("manifest.sqlite3",):
        legacy_path = source / legacy_name
        if legacy_path.exists():
            ensure_dir(manifest_destination.parent)
            _move_entry(legacy_path, manifest_destination)
            moved.append({"label": "kb.manifest", "from": str(legacy_path), "to": str(manifest_destination)})

    if source.exists() and not any(source.iterdir()):
        source.rmdir()
    return moved


def _move_object_dirs(source: Path, destination: Path, *, label: str) -> list[dict[str, str]]:
    moved: list[dict[str, str]] = []
    for dir_name in ("claims", "procedures", "cases", "decisions", "sources", "extracts", "lancedb"):
        src = source / dir_name
        if not src.exists():
            continue
        target = destination / dir_name if dir_name in {"claims", "procedures", "cases", "decisions"} else destination.parent / dir_name
        _move_entry(src, target)
        moved.append({"label": label, "from": str(src), "to": str(target)})
    return moved


def _move_tree(source: Path, destination: Path, *, label: str) -> list[dict[str, str]]:
    if not source.exists():
        return []
    if destination.exists() and any(destination.iterdir()):
        raise RuntimeError(f"Refusing to overwrite non-empty destination: {destination}")
    ensure_dir(destination.parent)
    _move_entry(source, destination)
    return [{"label": label, "from": str(source), "to": str(destination)}]


def _move_entry(source: Path, destination: Path) -> None:
    if destination.exists():
        raise RuntimeError(f"Refusing to overwrite existing destination: {destination}")
    ensure_dir(destination.parent)
    shutil.move(str(source), str(destination))


if __name__ == "__main__":
    main()
