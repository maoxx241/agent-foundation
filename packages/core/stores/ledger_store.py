from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from packages.core.events import LedgerEvent
from packages.core.storage.fs_utils import ensure_dir, utc_now


class LedgerStore:
    def __init__(self, root: Path):
        self.root = root
        self.task_events_root = self.root / "task_events"
        self.kb_events_root = self.root / "kb_events"
        self.audit_root = self.root / "audits"
        ensure_dir(self.task_events_root)
        ensure_dir(self.kb_events_root)
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
    ) -> LedgerEvent:
        event = LedgerEvent(
            event_id=str(uuid.uuid4()),
            entity_type="task",
            entity_id=task_id,
            event_type=event_type,
            actor=actor,
            timestamp=utc_now().isoformat(),
            trace_id=trace_id,
            run_id=run_id,
            payload=payload,
        )
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
    ) -> LedgerEvent:
        event = LedgerEvent(
            event_id=str(uuid.uuid4()),
            entity_type="kb",
            entity_id=object_id,
            event_type=event_type,
            actor=actor,
            timestamp=utc_now().isoformat(),
            trace_id=trace_id,
            run_id=run_id,
            payload=payload,
        )
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
    ) -> LedgerEvent:
        event = LedgerEvent(
            event_id=str(uuid.uuid4()),
            entity_type="audit",
            entity_id=entity_id,
            event_type=event_type,
            actor=actor,
            timestamp=utc_now().isoformat(),
            trace_id=trace_id,
            run_id=run_id,
            payload=payload,
        )
        date_key = event.timestamp[:10]
        self._append_jsonl(self.audit_root / f"{date_key}.jsonl", event.model_dump(mode="json"))
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
