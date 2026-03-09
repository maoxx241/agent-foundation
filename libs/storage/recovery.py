from __future__ import annotations

import io
import json
import shutil
import sqlite3
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Optional

from libs.storage.fs_utils import ValidationError, ensure_dir, utc_now
from .thin_kb_store import ThinKBStore


def backup_workspace(
    *,
    tasks_root: Path,
    kb_root: Path,
    output_path: Path,
    observability_root: Optional[Path] = None,
) -> dict[str, Any]:
    tasks_root = tasks_root.resolve()
    kb_root = kb_root.resolve()
    output_path = output_path.resolve()
    required = {
        "tasks": tasks_root,
        "kb/canonical": kb_root / "canonical",
        "kb/manifest.sqlite3": kb_root / "manifest.sqlite3",
    }
    missing = [name for name, path in required.items() if not path.exists()]
    if missing:
        raise ValidationError(f"Cannot create backup; missing required paths: {', '.join(missing)}")

    sections = [
        ("tasks", tasks_root),
        ("kb", kb_root),
    ]
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
        if observability_root is not None and (staging_root / "observability").exists():
            _replace_tree(staging_root / "observability", observability_root)

    store = ThinKBStore(kb_root=kb_root, db_path=kb_root / "manifest.sqlite3")
    rebuilt = store.rebuild_index()
    mismatch = detect_manifest_mismatch(kb_root=kb_root, db_path=store.db_path)
    if mismatch["missing_in_manifest"] or mismatch["missing_on_disk"]:
        raise ValidationError("Restore completed but manifest mismatch remains after rebuild")
    return {
        "archive_path": str(archive_path),
        "reindexed_objects": rebuilt,
        "tasks_root": str(tasks_root),
        "kb_root": str(kb_root),
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
