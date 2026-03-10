from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional, Tuple

from packages.core.schemas import ArtifactStage, TaskState
from .fs_utils import ConflictError, NotFoundError, read_json, read_text

STATE_ORDER = [
    TaskState.NEW,
    TaskState.EVIDENCE_READY,
    TaskState.DESIGN_APPROVED,
    TaskState.TESTSPEC_FROZEN,
    TaskState.IMPLEMENTED,
    TaskState.IMPL_APPROVED,
    TaskState.VALIDATED,
    TaskState.RELEASED,
    TaskState.WRITTEN_BACK,
]

NEXT_STATE = {
    TaskState.NEW: TaskState.EVIDENCE_READY,
    TaskState.EVIDENCE_READY: TaskState.DESIGN_APPROVED,
    TaskState.DESIGN_APPROVED: TaskState.TESTSPEC_FROZEN,
    TaskState.TESTSPEC_FROZEN: TaskState.IMPLEMENTED,
    TaskState.IMPLEMENTED: TaskState.IMPL_APPROVED,
    TaskState.IMPL_APPROVED: TaskState.VALIDATED,
    TaskState.VALIDATED: TaskState.RELEASED,
    TaskState.RELEASED: TaskState.WRITTEN_BACK,
}

ROLLBACKS = {
    TaskState.DESIGN_APPROVED: {TaskState.EVIDENCE_READY},
    TaskState.TESTSPEC_FROZEN: {TaskState.DESIGN_APPROVED},
    TaskState.IMPL_APPROVED: {TaskState.IMPLEMENTED},
    TaskState.VALIDATED: {TaskState.IMPLEMENTED, TaskState.DESIGN_APPROVED, TaskState.TESTSPEC_FROZEN},
    TaskState.RELEASED: {TaskState.VALIDATED, TaskState.IMPLEMENTED, TaskState.DESIGN_APPROVED, TaskState.TESTSPEC_FROZEN},
    TaskState.WRITTEN_BACK: {TaskState.RELEASED, TaskState.VALIDATED, TaskState.IMPLEMENTED, TaskState.DESIGN_APPROVED, TaskState.TESTSPEC_FROZEN},
}


def is_state_at_least(current: TaskState, minimum: TaskState) -> bool:
    return STATE_ORDER.index(current) >= STATE_ORDER.index(minimum)


def validate_transition(task_root: Path, current: TaskState, target: TaskState) -> None:
    if current == target:
        raise ConflictError(f"Task is already in state {current.value}")

    if NEXT_STATE.get(current) == target:
        _validate_gate(task_root, target)
        return

    if target in ROLLBACKS.get(current, set()):
        _validate_gate(task_root, target)
        return

    raise ConflictError(f"Illegal transition: {current.value} -> {target.value}")


def _validate_gate(task_root: Path, target: TaskState) -> None:
    if target == TaskState.EVIDENCE_READY:
        _require_any(task_root / ArtifactStage.task.value, "task-brief.json")
        _require_any(task_root / ArtifactStage.evidence.value, "evidence-pack.json")
        return

    if target == TaskState.DESIGN_APPROVED:
        _require_one_of(task_root / ArtifactStage.design.value, "design-spec.json", "design-spec.md")
        verdict, conditions_resolved = _review_gate(
            task_root / ArtifactStage.design.value,
            "design-review.json",
            "design-review.md",
        )
        if verdict not in {"approve", "approve_with_conditions"} or not conditions_resolved:
            raise ConflictError("Design review is not approved or has unresolved conditions")
        return

    if target == TaskState.TESTSPEC_FROZEN:
        _require_any(task_root / ArtifactStage.test.value, "test-spec.json")
        _require_any(task_root / ArtifactStage.test.value, "acceptance.json")
        return

    if target == TaskState.IMPLEMENTED:
        _require_any(task_root / ArtifactStage.dev.value, "patch.diff")
        _require_any(task_root / ArtifactStage.dev.value, "changed-files.json")
        _require_any(task_root / ArtifactStage.dev.value, "selftest.json")
        return

    if target == TaskState.IMPL_APPROVED:
        verdict, conditions_resolved = _review_gate(
            task_root / ArtifactStage.review.value,
            "impl-review.json",
            "impl-review.md",
        )
        if verdict not in {"approve", "approve_with_conditions"} or not conditions_resolved:
            raise ConflictError("Implementation review is not approved or has unresolved conditions")
        return

    if target == TaskState.VALIDATED:
        validation_path = _require_any(task_root / ArtifactStage.validation.value, "validation-report.json")
        _require_any(task_root / ArtifactStage.validation.value, "regression.json")
        payload = read_json(validation_path)
        if payload.get("passed") is not True:
            suggested = suggested_rollback_target(payload)
            if suggested is None:
                raise ConflictError("validation-report.json must indicate passed=true before VALIDATED")
            raise ConflictError(
                f"validation-report.json must indicate passed=true before VALIDATED; "
                f"suggested rollback target: {suggested.value}"
            )
        return

    if target == TaskState.RELEASED:
        _require_one_of(task_root / ArtifactStage.release.value, "adr.json", "adr.md")
        _require_any(task_root / ArtifactStage.release.value, "changelog.md")
        return

    if target == TaskState.WRITTEN_BACK:
        _require_any(task_root / ArtifactStage.writeback.value, "experience-packet.json")
        _require_any(task_root / ArtifactStage.writeback.value, "finalization.json")
        return


def _require_any(stage_dir: Path, name: str) -> Path:
    path = stage_dir / name
    if not path.exists():
        raise ConflictError(f"Required artifact missing: {stage_dir.name}/{name}")
    return path


def _require_one_of(stage_dir: Path, *names: str) -> Path:
    for name in names:
        path = stage_dir / name
        if path.exists():
            return path
    rendered = ", ".join(f"{stage_dir.name}/{name}" for name in names)
    raise ConflictError(f"Required artifact missing: one of {rendered}")


def _review_gate(stage_dir: Path, json_name: str, markdown_name: str) -> Tuple[Optional[str], bool]:
    json_path = stage_dir / json_name
    if json_path.exists():
        payload = read_json(json_path)
        verdict = str(payload.get("verdict", "")).strip()
        required_changes = payload.get("required_changes", []) or []
        return verdict, verdict != "approve_with_conditions" or len(required_changes) == 0

    markdown_path = stage_dir / markdown_name
    if not markdown_path.exists():
        raise ConflictError(f"Required artifact missing: {stage_dir.name}/{json_name} or {stage_dir.name}/{markdown_name}")

    content = read_text(markdown_path)
    verdict = _extract_markdown_field(content, "verdict")
    resolved = _extract_markdown_field(content, "conditions_resolved")
    if verdict == "approve_with_conditions":
        return verdict, resolved == "true"
    return verdict, verdict == "approve"


def _extract_markdown_field(content: str, field_name: str) -> Optional[str]:
    pattern = rf"(?im)^\s*{re.escape(field_name)}\s*:\s*(.+?)\s*$"
    match = re.search(pattern, content)
    if not match:
        return None
    return match.group(1).strip()


def load_review_payload(path: Path) -> Any:
    if path.suffix == ".json":
        return read_json(path)
    if path.suffix in {".md", ".txt"}:
        return read_text(path)
    raise NotFoundError(f"Unsupported review artifact format: {path.name}")


def suggested_rollback_target(validation_payload: dict[str, Any]) -> Optional[TaskState]:
    classification = str(validation_payload.get("root_cause_classification", "")).strip()
    return {
        "implementation_defect": TaskState.IMPLEMENTED,
        "design_ambiguity": TaskState.DESIGN_APPROVED,
        "testspec_weakness": TaskState.TESTSPEC_FROZEN,
    }.get(classification)
