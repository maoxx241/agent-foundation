from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional, Type

from pydantic import BaseModel, ValidationError as PydanticValidationError

from packages.core.migrations.registry import apply_artifact_payload_migrations
from packages.core.schemas import ArtifactStage, TaskBrief, TaskState, TaskStateRecord
from packages.core.schemas.artifacts import (
    ADR,
    DesignReview,
    DesignSpec,
    EvidencePack,
    ExperiencePacket,
    ImplReview,
    PatchBundle,
    SelfTestReport,
    TestSpec,
    ValidationReport,
)
from .fs_utils import ConflictError, NotFoundError, ValidationError, ensure_dir, list_files, read_json, read_text, utc_now, write_json_atomic, write_text_atomic
from .fs_utils import safe_child
from .state_machine import is_state_at_least, validate_transition

SCHEMA_MODELS: dict[str, Type[BaseModel]] = {
    "task-brief.json": TaskBrief,
    "evidence-pack.json": EvidencePack,
    "design-spec.json": DesignSpec,
    "design-review.json": DesignReview,
    "test-spec.json": TestSpec,
    "patch-bundle.json": PatchBundle,
    "selftest.json": SelfTestReport,
    "impl-review.json": ImplReview,
    "validation-report.json": ValidationReport,
    "adr.json": ADR,
    "experience-packet.json": ExperiencePacket,
}

GENERIC_JSON_FILES = {
    "acceptance.json",
    "attachments.json",
    "changed-files.json",
    "finalization.json",
    "gaps.json",
    "perf.json",
    "regression.json",
}

INTERNAL_ONLY_FILES = {"state.json", "finalization.json"}

ALLOWED_STAGE_FILES = {
    ArtifactStage.task.value: {"task-brief.json", "state.json"},
    ArtifactStage.evidence.value: {"evidence-pack.json", "gaps.json"},
    ArtifactStage.design.value: {"design-main.md", "design-alt.md", "design-spec.md", "design-spec.json", "design-review.md", "design-review.json"},
    ArtifactStage.test.value: {"test-spec.json", "acceptance.json"},
    ArtifactStage.dev.value: {"patch.diff", "patch-bundle.json", "changed-files.json", "selftest.json", "dev-notes.md"},
    ArtifactStage.review.value: {"impl-review.md", "impl-review.json"},
    ArtifactStage.validation.value: {"validation-report.json", "regression.json", "perf.json"},
    ArtifactStage.release.value: {"adr.md", "adr.json", "changelog.md", "incident-summary.md"},
    ArtifactStage.writeback.value: {"experience-packet.json", "attachments.json", "finalization.json"},
}


class ArtifactStore:
    def __init__(self, tasks_root: Path):
        self.tasks_root = tasks_root
        self.active_root = self.tasks_root / "active"
        self.archived_root = self.tasks_root / "archived"
        ensure_dir(self.active_root)
        ensure_dir(self.archived_root)

    def create_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        task_id = str(payload.get("task_id", "")).strip()
        if not task_id:
            raise ValidationError("task_id is required")

        task_root = self.task_root(task_id)
        if task_root.exists():
            raise ConflictError(f"Task already exists: {task_id}")

        now = utc_now()
        task_payload = dict(payload)
        task_payload.setdefault("created_at", now.isoformat())
        task_payload["updated_at"] = now.isoformat()
        try:
            task_brief = TaskBrief.model_validate(task_payload).model_dump(mode="json")
        except PydanticValidationError as exc:
            raise ValidationError(str(exc)) from exc

        state_record = TaskStateRecord(
            task_id=task_id,
            state=TaskState.NEW,
            previous_state=None,
            changed_by="system",
            reason="Task created",
            created_at=now,
            updated_at=now,
        ).model_dump(mode="json")

        staging_root = Path(tempfile.mkdtemp(prefix=f".task-{task_id}-", dir=self.active_root))
        try:
            for stage in ArtifactStage:
                ensure_dir(staging_root / stage.value)
            write_json_atomic(staging_root / ArtifactStage.task.value / "task-brief.json", task_brief)
            write_json_atomic(staging_root / ArtifactStage.task.value / "state.json", state_record)
            try:
                staging_root.replace(task_root)
            except OSError as exc:
                raise ConflictError(f"Task already exists: {task_id}") from exc
        except Exception:
            if staging_root.exists():
                shutil.rmtree(staging_root, ignore_errors=True)
            raise

        return self.get_task(task_id)

    def get_task(self, task_id: str) -> dict[str, Any]:
        task_root = self.task_root(task_id)
        if not task_root.exists():
            raise NotFoundError(f"Task not found: {task_id}")

        task_brief = self._read_artifact_json(task_root / ArtifactStage.task.value / "task-brief.json", "task-brief.json")
        state = self._read_artifact_json(task_root / ArtifactStage.task.value / "state.json", "state.json")
        artifacts = self.list_artifacts(task_id)
        return {
            "task": task_brief,
            "state": state,
            "artifacts": artifacts,
        }

    def bundle_task(self, task_id: str) -> dict[str, Any]:
        task = self.get_task(task_id)
        flattened: list[dict[str, Any]] = []
        for stage, artifacts in task["artifacts"].items():
            for artifact in artifacts:
                flattened.append({"stage": stage, **artifact})
        return {
            "task_id": task_id,
            "state": task["state"]["state"],
            "task": task["task"],
            "artifacts": flattened,
        }

    def list_artifacts(self, task_id: str) -> dict[str, list[dict[str, Any]]]:
        task_root = self.task_root(task_id)
        if not task_root.exists():
            raise NotFoundError(f"Task not found: {task_id}")

        result: dict[str, list[dict[str, Any]]] = {}
        for stage in ArtifactStage:
            stage_dir = task_root / stage.value
            result[stage.value] = [
                {
                    "name": entry.name,
                    "format": infer_format(entry.name),
                    "size_bytes": entry.stat().st_size,
                }
                for entry in list_files(stage_dir)
            ]
        return result

    def get_artifact(self, task_id: str, stage: str, name: str) -> dict[str, Any]:
        path = self._artifact_path(task_id, stage, name)
        fmt = infer_format(name)
        content = read_json(path) if fmt == "json" else read_text(path)
        return {
            "task_id": task_id,
            "stage": stage,
            "name": name,
            "format": fmt,
            "content": content,
        }

    def put_artifact(self, task_id: str, stage: str, name: str, payload_format: str, content: Any) -> dict[str, Any]:
        self._validate_name(stage, name)
        if name in INTERNAL_ONLY_FILES:
            raise ValidationError(f"{name} is managed by the service and cannot be written directly")

        path = self._artifact_path(task_id, stage, name)
        validated_content = self._validate_content(task_id, path, name, payload_format, content)
        if payload_format == "json":
            write_json_atomic(path, validated_content)
        else:
            write_text_atomic(path, validated_content)
        return self.get_artifact(task_id, stage, name)

    def update_state(self, task_id: str, target_state: TaskState, changed_by: str, reason: Optional[str] = None) -> dict[str, Any]:
        task_root = self.task_root(task_id)
        current_state_record = self.get_state(task_id)
        current_state = TaskState(current_state_record["state"])
        target_state = TaskState(target_state)
        if current_state == target_state:
            raise ConflictError(f"Task {task_id} is already in state {target_state.value}")
        validate_transition(task_root, current_state, target_state)

        now = utc_now()
        new_record = TaskStateRecord(
            task_id=task_id,
            state=target_state,
            previous_state=current_state,
            changed_by=changed_by,
            reason=reason,
            created_at=current_state_record["created_at"],
            updated_at=now,
        )
        write_json_atomic(task_root / ArtifactStage.task.value / "state.json", new_record.model_dump(mode="json"))
        return self.get_task(task_id)

    def finalize_experience(self, task_id: str, finalized_by: str = "system") -> dict[str, Any]:
        state_record = self.get_state(task_id)
        current_state = TaskState(state_record["state"])
        if not is_state_at_least(current_state, TaskState.VALIDATED):
            raise ConflictError("ExperiencePacket cannot be finalized before VALIDATED")

        task_root = self.task_root(task_id)
        experience_path = task_root / ArtifactStage.writeback.value / "experience-packet.json"
        finalization_path = task_root / ArtifactStage.writeback.value / "finalization.json"
        if not experience_path.exists():
            raise ConflictError("experience-packet.json is required before finalization")

        if finalization_path.exists():
            marker = read_json(finalization_path)
            current_state = TaskState(self.get_state(task_id)["state"])
            if is_state_at_least(current_state, TaskState.RELEASED) and current_state != TaskState.WRITTEN_BACK:
                self.update_state(task_id, TaskState.WRITTEN_BACK, finalized_by, "Experience packet finalized")
            return {
                "task_id": task_id,
                "state": self.get_state(task_id)["state"],
                "finalization": marker,
            }

        now = utc_now()
        marker = {
            "task_id": task_id,
            "finalized_at": now.isoformat(),
            "finalized_by": finalized_by,
            "state_at_finalize": current_state.value,
        }
        write_json_atomic(finalization_path, marker)

        if is_state_at_least(current_state, TaskState.RELEASED) and current_state != TaskState.WRITTEN_BACK:
            self.update_state(task_id, TaskState.WRITTEN_BACK, finalized_by, "Experience packet finalized")

        return {
            "task_id": task_id,
            "state": self.get_state(task_id)["state"],
            "finalization": marker,
        }

    def get_state(self, task_id: str) -> dict[str, Any]:
        task_root = self.task_root(task_id)
        return self._read_artifact_json(task_root / ArtifactStage.task.value / "state.json", "state.json")

    def archive_task(self, task_id: str, *, archived_by: str, reason: Optional[str] = None) -> dict[str, Any]:
        source = self.task_root(task_id)
        if not source.exists():
            raise NotFoundError(f"Task not found: {task_id}")

        destination = safe_child(self.archived_root, task_id, field_name="task_id")
        if destination.exists():
            raise ConflictError(f"Archived task already exists: {task_id}")

        ensure_dir(destination.parent)
        source.replace(destination)
        return {
            "task_id": task_id,
            "archived_by": archived_by,
            "reason": reason,
            "archived_root": str(destination),
        }

    def task_root(self, task_id: str) -> Path:
        return safe_child(self.active_root, task_id, field_name="task_id")

    def _artifact_path(self, task_id: str, stage: str, name: str) -> Path:
        task_root = self.task_root(task_id)
        if not task_root.exists():
            raise NotFoundError(f"Task not found: {task_id}")
        self._validate_name(stage, name)
        return safe_child(task_root / stage, name, field_name="artifact name")

    def _validate_name(self, stage: str, name: str) -> None:
        allowed = ALLOWED_STAGE_FILES.get(stage)
        if allowed is None:
            raise ValidationError(f"Unknown artifact stage: {stage}")
        if name not in allowed:
            raise ValidationError(f"Artifact name '{name}' is not allowed in stage '{stage}'")

    def _validate_content(self, task_id: str, path: Path, name: str, payload_format: str, content: Any) -> Any:
        expected_format = infer_format(name)
        if payload_format != expected_format:
            raise ValidationError(f"{name} requires format '{expected_format}'")

        if payload_format == "json":
            if not isinstance(content, (dict, list)):
                raise ValidationError("JSON artifacts require an object or array payload")

            if name in SCHEMA_MODELS:
                if not isinstance(content, dict):
                    raise ValidationError(f"{name} requires a JSON object")
                existing = read_json(path) if path.exists() else None
                payload = dict(content)
                payload.setdefault("task_id", task_id)
                if existing and "created_at" in existing:
                    payload.setdefault("created_at", existing["created_at"])
                else:
                    payload.setdefault("created_at", utc_now().isoformat())
                payload["updated_at"] = utc_now().isoformat()
                try:
                    model = SCHEMA_MODELS[name].model_validate(payload)
                except PydanticValidationError as exc:
                    raise ValidationError(str(exc)) from exc
                return model.model_dump(mode="json")

            if name in GENERIC_JSON_FILES:
                return content

            raise ValidationError(f"No validation rule is defined for {name}")

        if not isinstance(content, str):
            raise ValidationError("Text and markdown artifacts require string content")
        return content

    def _read_artifact_json(self, path: Path, name: str) -> Any:
        payload = read_json(path)
        if isinstance(payload, dict):
            migrated, applied = apply_artifact_payload_migrations(name, payload)
            if applied:
                write_json_atomic(path, migrated)
            return migrated
        return payload


def infer_format(name: str) -> str:
    if name.endswith(".json"):
        return "json"
    if name.endswith(".md"):
        return "markdown"
    return "text"
