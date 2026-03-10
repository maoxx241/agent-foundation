from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from packages.core.events import AuditEvent, KBEvent, LedgerEvent, ReleaseEvent, ReplayRunEvent, TaskEvent
from packages.core.storage.fs_utils import append_jsonl_line, ensure_dir, safe_child, utc_now, validate_storage_identifier


class LedgerStore:
    def __init__(self, root: Path):
        self.root = root
        self.task_events_root = self.root / "task_events"
        self.kb_events_root = self.root / "kb_events"
        self.replay_runs_root = self.root / "replay_runs"
        self.release_root = self.root / "releases"
        self.audit_root = self.root / "audits"
        ensure_dir(self.task_events_root)
        ensure_dir(self.kb_events_root)
        ensure_dir(self.replay_runs_root)
        ensure_dir(self.release_root)
        ensure_dir(self.audit_root)

    def append_task_event(
        self,
        task_id: str,
        event_type: str,
        *,
        actor: str | None = None,
        trace_id: str | None = None,
        run_id: str | None = None,
        **payload: Any,
    ) -> TaskEvent:
        event = TaskEvent(**self._event_fields("task", task_id, event_type, actor, trace_id, run_id, payload))
        self._append_jsonl(self._event_path(self.task_events_root, task_id, field_name="task_id"), event.model_dump(mode="json"))
        return event

    def append_kb_event(
        self,
        object_id: str,
        event_type: str,
        *,
        actor: str | None = None,
        trace_id: str | None = None,
        run_id: str | None = None,
        **payload: Any,
    ) -> KBEvent:
        event = KBEvent(**self._event_fields("kb", object_id, event_type, actor, trace_id, run_id, payload))
        self._append_jsonl(self._event_path(self.kb_events_root, object_id, field_name="object_id"), event.model_dump(mode="json"))
        return event

    def append_audit_event(
        self,
        entity_id: str,
        event_type: str,
        *,
        actor: str | None = None,
        trace_id: str | None = None,
        run_id: str | None = None,
        **payload: Any,
    ) -> AuditEvent:
        event = AuditEvent(**self._event_fields("audit", entity_id, event_type, actor, trace_id, run_id, payload))
        date_key = event.timestamp[:10]
        self._append_jsonl(self.audit_root / f"{date_key}.jsonl", event.model_dump(mode="json"))
        return event

    def append_replay_run_event(
        self,
        run_id_value: str,
        event_type: str,
        *,
        actor: str | None = None,
        trace_id: str | None = None,
        run_id: str | None = None,
        **payload: Any,
    ) -> ReplayRunEvent:
        event = ReplayRunEvent(
            **self._event_fields("replay_run", run_id_value, event_type, actor, trace_id, run_id or run_id_value, payload)
        )
        self._append_jsonl(self._event_path(self.replay_runs_root, run_id_value, field_name="run_id"), event.model_dump(mode="json"))
        return event

    def append_release_event(
        self,
        release_id: str,
        event_type: str,
        *,
        actor: str | None = None,
        trace_id: str | None = None,
        run_id: str | None = None,
        **payload: Any,
    ) -> ReleaseEvent:
        event = ReleaseEvent(**self._event_fields("release", release_id, event_type, actor, trace_id, run_id, payload))
        self._append_jsonl(self._event_path(self.release_root, release_id, field_name="release_id"), event.model_dump(mode="json"))
        return event

    def read_task_events(self, task_id: str) -> list[LedgerEvent]:
        return self._read_events(self._event_path(self.task_events_root, task_id, field_name="task_id"))

    def read_kb_events(self, object_id: str) -> list[LedgerEvent]:
        return self._read_events(self._event_path(self.kb_events_root, object_id, field_name="object_id"))

    def read_audit_events(self) -> list[LedgerEvent]:
        events: list[LedgerEvent] = []
        for path in sorted(self.audit_root.glob("*.jsonl")):
            events.extend(self._read_events(path))
        return events

    def read_replay_run_events(self, run_id_value: str) -> list[LedgerEvent]:
        return self._read_events(self._event_path(self.replay_runs_root, run_id_value, field_name="run_id"))

    def read_release_events(self, release_id: str) -> list[LedgerEvent]:
        return self._read_events(self._event_path(self.release_root, release_id, field_name="release_id"))

    def _read_events(self, path: Path) -> list[LedgerEvent]:
        if not path.exists():
            return []
        events: list[LedgerEvent] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            events.append(LedgerEvent.model_validate_json(line))
        return events

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        append_jsonl_line(path, payload)

    def _event_path(self, root: Path, identifier: str, *, field_name: str) -> Path:
        validate_storage_identifier(identifier, field_name=field_name)
        return safe_child(root, f"{identifier}.jsonl", field_name=f"{field_name} ledger file")

    def _event_fields(
        self,
        entity_type: str,
        entity_id: str,
        event_type: str,
        actor: str | None,
        trace_id: str | None,
        run_id: str | None,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "event_id": str(uuid.uuid4()),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "event_type": event_type,
            "actor": actor,
            "timestamp": utc_now().isoformat(),
            "trace_id": trace_id,
            "run_id": run_id,
            "payload": payload,
        }
