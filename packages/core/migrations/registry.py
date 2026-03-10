from __future__ import annotations

from copy import deepcopy
from typing import Any


ARTIFACT_SCHEMA_VERSION = "1.0"
KB_SCHEMA_VERSION = "1.0"


def apply_artifact_payload_migrations(name: str, payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    migrated = deepcopy(payload)
    applied: list[str] = []
    if _is_schema_backed_artifact(name) and "artifact_schema_version" not in migrated:
        migrated["artifact_schema_version"] = ARTIFACT_SCHEMA_VERSION
        applied.append("artifact_schema_version@1.0")
    return migrated, applied


def apply_kb_payload_migrations(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    migrated = deepcopy(payload)
    applied: list[str] = []
    if "schema_version" not in migrated:
        migrated["schema_version"] = KB_SCHEMA_VERSION
        applied.append("schema_version@1.0")
    if "object_revision" not in migrated:
        migrated["object_revision"] = 1
        applied.append("object_revision@1")
    if "supersedes" not in migrated:
        migrated["supersedes"] = []
        applied.append("supersedes@[]")
    if "deprecated_reason" not in migrated:
        migrated["deprecated_reason"] = None
        applied.append("deprecated_reason@null")
    if "promotion_source" not in migrated:
        migrated["promotion_source"] = {}
        applied.append("promotion_source@{}")
    return migrated, applied


def _is_schema_backed_artifact(name: str) -> bool:
    return name.endswith(".json") and name not in {
        "acceptance.json",
        "attachments.json",
        "changed-files.json",
        "finalization.json",
        "gaps.json",
        "perf.json",
        "regression.json",
    }
