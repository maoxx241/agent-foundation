from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class StorageError(Exception):
    """Base storage error."""


class NotFoundError(StorageError):
    """Raised when a requested file or object does not exist."""


class ConflictError(StorageError):
    """Raised when a requested write or state transition conflicts with current state."""


class ValidationError(StorageError):
    """Raised when input fails service-side validation."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Any:
    if not path.exists():
        raise NotFoundError(f"File not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.exists():
        raise NotFoundError(f"File not found: {path}")
    return path.read_text(encoding="utf-8")


def write_json_atomic(path: Path, payload: Any) -> None:
    write_text_atomic(path, json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n")


def write_text_atomic(path: Path, payload: str) -> None:
    ensure_dir(path.parent)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as handle:
        handle.write(payload)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def list_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted([entry for entry in path.iterdir() if entry.is_file()])

