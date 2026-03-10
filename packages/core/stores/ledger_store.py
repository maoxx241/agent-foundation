from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from packages.core.events import AuditEvent, KBEvent, LedgerEvent, ReleaseEvent, ReplayRunEvent, TaskEvent
from packages.core.storage.fs_utils import ensure_dir, utc_now


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
        self._append_jsonl(self.task_events_root / f"{task_id}.jsonl", event.model_dump(mode="json"))
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
        self._append_jsonl(self.kb_events_root / f"{object_id}.jsonl", event.model_dump(mode="json"))
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
        self._append_jsonl(self.replay_runs_root / f"{run_id_value}.jsonl", event.model_dump(mode="json"))
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
        self._append_jsonl(self.release_root / f"{release_id}.jsonl", event.model_dump(mode="json"))
        return event

    def read_task_events(self, task_id: str) -> list[LedgerEvent]:
        return self._read_events(self.task_events_root / f"{task_id}.jsonl")

    def read_kb_events(self, object_id: str) -> list[LedgerEvent]:
        return self._read_events(self.kb_events_root / f"{object_id}.jsonl")

    def read_audit_events(self) -> list[LedgerEvent]:
        events: list[LedgerEvent] = []
        for path in sorted(self.audit_root.glob("*.jsonl")):
            events.extend(self._read_events(path))
        return events

    def read_replay_run_events(self, run_id_value: str) -> list[LedgerEvent]:
        return self._read_events(self.replay_runs_root / f"{run_id_value}.jsonl")

    def read_release_events(self, release_id: str) -> list[LedgerEvent]:
        return self._read_events(self.release_root / f"{release_id}.jsonl")

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
        ensure_dir(path.parent)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n")

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
