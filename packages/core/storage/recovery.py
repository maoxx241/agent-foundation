from __future__ import annotations

import io
import json
import shutil
import sqlite3
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Optional

from packages.core.storage.fs_utils import ValidationError, ensure_dir, utc_now
from .thin_kb_store import ThinKBStore


def backup_workspace(
    *,
    tasks_root: Path,
    kb_root: Path,
    output_path: Path,
    indexes_root: Optional[Path] = None,
    ledgers_root: Optional[Path] = None,
    replay_root: Optional[Path] = None,
    backups_root: Optional[Path] = None,
    observability_root: Optional[Path] = None,
) -> dict[str, Any]:
    tasks_root = tasks_root.resolve()
    kb_root = kb_root.resolve()
    output_path = output_path.resolve()
    indexes_root = indexes_root.resolve() if indexes_root is not None else None
    ledgers_root = ledgers_root.resolve() if ledgers_root is not None else None
    replay_root = replay_root.resolve() if replay_root is not None else None
    backups_root = backups_root.resolve() if backups_root is not None else None
    manifest_db_path = _manifest_db_path(kb_root=kb_root, indexes_root=indexes_root)
    required = {
        "tasks": tasks_root,
        "kb/canonical": kb_root / "canonical",
        str(_archive_name_for_path(manifest_db_path, kb_root, indexes_root)): manifest_db_path,
    }
    missing = [name for name, path in required.items() if not path.exists()]
    if missing:
        raise ValidationError(f"Cannot create backup; missing required paths: {', '.join(missing)}")

    sections = [
        ("tasks", tasks_root),
        ("kb", kb_root),
    ]
    if indexes_root is not None and indexes_root.exists():
        sections.append(("indexes", indexes_root))
    if ledgers_root is not None and ledgers_root.exists():
        sections.append(("ledgers", ledgers_root))
    if replay_root is not None and replay_root.exists():
        sections.append(("replay", replay_root))
    if backups_root is not None and backups_root.exists() and not output_path.is_relative_to(backups_root):
        sections.append(("backups", backups_root))
    if observability_root is not None and observability_root.exists():
        sections.append(("observability", observability_root.resolve()))

    manifest = {
        "created_at": utc_now().isoformat(),
        "sections": [
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
            }
            for name, path in sections
        ],
    }
    ensure_dir(output_path.parent)
    with tarfile.open(output_path, "w:gz") as archive:
        manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
        info = tarfile.TarInfo(name="manifest.json")
        info.size = len(manifest_bytes)
        archive.addfile(info, io.BytesIO(manifest_bytes))
        for name, path in sections:
            archive.add(path, arcname=name)

    return {
        "archive_path": str(output_path),
        "sections": [name for name, _ in sections],
    }


def restore_workspace(
    *,
    archive_path: Path,
    tasks_root: Path,
    kb_root: Path,
    indexes_root: Optional[Path] = None,
    ledgers_root: Optional[Path] = None,
    replay_root: Optional[Path] = None,
    backups_root: Optional[Path] = None,
    observability_root: Optional[Path] = None,
) -> dict[str, Any]:
    archive_path = archive_path.resolve()
    if not archive_path.exists():
        raise ValidationError(f"Backup archive not found: {archive_path}")

    with tempfile.TemporaryDirectory() as temp_dir:
        staging_root = Path(temp_dir)
        with tarfile.open(archive_path, "r:gz") as archive:
            _safe_extractall(archive, staging_root)

        if not (staging_root / "manifest.json").exists():
            raise ValidationError("Backup archive missing manifest.json")
        if not (staging_root / "tasks").exists():
            raise ValidationError("Backup archive missing tasks/ content")
        if not (staging_root / "kb" / "canonical").exists():
            raise ValidationError("Backup archive missing kb/canonical content")

        _replace_tree(staging_root / "tasks", tasks_root)
        _replace_tree(staging_root / "kb", kb_root)
        if indexes_root is not None and (staging_root / "indexes").exists():
            _replace_tree(staging_root / "indexes", indexes_root)
        if ledgers_root is not None and (staging_root / "ledgers").exists():
            _replace_tree(staging_root / "ledgers", ledgers_root)
        if replay_root is not None and (staging_root / "replay").exists():
            _replace_tree(staging_root / "replay", replay_root)
        if backups_root is not None and (staging_root / "backups").exists():
            _replace_tree(staging_root / "backups", backups_root)
        if observability_root is not None and (staging_root / "observability").exists():
            _replace_tree(staging_root / "observability", observability_root)

    db_path = _manifest_db_path(kb_root=kb_root, indexes_root=indexes_root)
    store = ThinKBStore(kb_root=kb_root, db_path=db_path)
    rebuilt = store.rebuild_index()
    mismatch = detect_manifest_mismatch(kb_root=kb_root, db_path=store.db_path)
    if mismatch["missing_in_manifest"] or mismatch["missing_on_disk"]:
        raise ValidationError("Restore completed but manifest mismatch remains after rebuild")
    return {
        "archive_path": str(archive_path),
        "reindexed_objects": rebuilt,
        "tasks_root": str(tasks_root),
        "kb_root": str(kb_root),
        "db_path": str(db_path),
    }


def detect_manifest_mismatch(*, kb_root: Path, db_path: Path) -> dict[str, list[str]]:
    file_ids: set[str] = set()
    canonical_root = kb_root / "canonical"
    for path in canonical_root.glob("*/*.json"):
        file_ids.add(path.stem)

    db_ids: set[str] = set()
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        try:
            db_ids = {row[0] for row in conn.execute("SELECT id FROM kb_objects").fetchall()}
        finally:
            conn.close()

    return {
        "missing_in_manifest": sorted(file_ids - db_ids),
        "missing_on_disk": sorted(db_ids - file_ids),
    }


def _replace_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    ensure_dir(destination.parent)
    shutil.copytree(source, destination)


def _safe_extractall(archive: tarfile.TarFile, destination: Path) -> None:
    destination = destination.resolve()
    for member in archive.getmembers():
        target = (destination / member.name).resolve()
        if not str(target).startswith(str(destination)):
            raise ValidationError(f"Unsafe archive member path: {member.name}")
    archive.extractall(destination)


def _manifest_db_path(*, kb_root: Path, indexes_root: Optional[Path]) -> Path:
    if indexes_root is not None:
        candidate = indexes_root / "sqlite" / "manifest.sqlite3"
        if candidate.exists() or not (kb_root / "manifest.sqlite3").exists():
            return candidate
    return kb_root / "manifest.sqlite3"


def _archive_name_for_path(path: Path, kb_root: Path, indexes_root: Optional[Path]) -> str:
    if indexes_root is not None and path.is_relative_to(indexes_root):
        return f"indexes/{path.relative_to(indexes_root)}"
    return f"kb/{path.relative_to(kb_root)}"
