from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


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


def validate_storage_identifier(value: str, *, field_name: str = "identifier") -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValidationError(f"{field_name} is required")
    if normalized in {".", ".."}:
        raise ValidationError(f"{field_name} must be a single safe path segment")

    candidate = Path(normalized)
    if candidate.name != normalized or len(candidate.parts) != 1:
        raise ValidationError(f"{field_name} must be a single safe path segment")

    for separator in {os.sep, os.altsep}:
        if separator and separator in normalized:
            raise ValidationError(f"{field_name} must be a single safe path segment")

    reserved = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
    if normalized.upper() in reserved:
        raise ValidationError(f"{field_name} uses a reserved filesystem name")

    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    if any(char not in allowed for char in normalized):
        raise ValidationError(f"{field_name} may contain only letters, numbers, '.', '_' and '-'")
    return normalized


def safe_child(root: Path, name: str, *, field_name: str = "path segment") -> Path:
    normalized = validate_storage_identifier(name, field_name=field_name)
    child = (root / normalized).resolve()
    if not child.is_relative_to(root.resolve()):
        raise ValidationError(f"{field_name} must remain within {root}")
    return child


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


def append_jsonl_line(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    line = json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n"
    with _locked_append_handle(path) as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def list_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted([entry for entry in path.iterdir() if entry.is_file()])


@contextmanager
def _locked_append_handle(path: Path) -> Iterator[Any]:
    with path.open("a", encoding="utf-8") as handle:
        _lock_file(handle)
        try:
            yield handle
        finally:
            _unlock_file(handle)


def _lock_file(handle: Any) -> None:
    if os.name == "nt":  # pragma: no cover - exercised on Windows
        import msvcrt

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        return

    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)


def _unlock_file(handle: Any) -> None:
    if os.name == "nt":  # pragma: no cover - exercised on Windows
        import msvcrt

        handle.flush()
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return

    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
