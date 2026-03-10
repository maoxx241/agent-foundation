from __future__ import annotations

from packages.core.events import TaskAuditReport
from packages.core.stores.artifact_store import ArtifactStore
from packages.core.stores.ledger_store import LedgerStore
from packages.core.storage.fs_utils import ConflictError, NotFoundError, ValidationError


class ArtifactService:
    def __init__(self, store: ArtifactStore, ledger_store: LedgerStore):
        self.store = store
        self.ledger_store = ledger_store

    def create_task(self, payload: dict, *, actor: str, trace_id: str | None = None, run_id: str | None = None) -> dict:
        task_id = str(payload.get("task_id", "")).strip()
        try:
            result = self.store.create_task(payload)
        except (ConflictError, ValidationError) as exc:
            self.ledger_store.append_task_event(
                task_id or "unknown-task",
                "task_create_rejected",
                actor=actor,
                trace_id=trace_id,
                run_id=run_id,
                reason=str(exc),
            )
            raise
        self.ledger_store.append_task_event(
            task_id,
            "task_created",
            actor=actor,
            trace_id=trace_id,
            run_id=run_id,
            project_id=payload.get("project_id"),
        )
        return result

    def get_task(self, task_id: str) -> dict:
        return self.store.get_task(task_id)

    def bundle_task(self, task_id: str) -> dict:
        return self.store.bundle_task(task_id)

    def list_artifacts(self, task_id: str) -> dict[str, list[dict]]:
        return self.store.list_artifacts(task_id)

    def get_artifact(self, task_id: str, stage: str, name: str) -> dict:
        return self.store.get_artifact(task_id, stage, name)

    def put_artifact(
        self,
        task_id: str,
        stage: str,
        name: str,
        payload_format: str,
        content,
        *,
        actor: str,
        trace_id: str | None = None,
        run_id: str | None = None,
    ) -> dict:
        result = self.store.put_artifact(task_id, stage, name, payload_format, content)
        self.ledger_store.append_task_event(
            task_id,
            "artifact_written",
            actor=actor,
            trace_id=trace_id,
            run_id=run_id,
            stage=stage,
            name=name,
            format=payload_format,
        )
        return result

    def update_state(
        self,
        task_id: str,
        target_state,
        changed_by: str,
        reason: str | None = None,
        *,
        trace_id: str | None = None,
        run_id: str | None = None,
    ) -> dict:
        previous = self.store.get_state(task_id)["state"]
        target_state_value = getattr(target_state, "value", str(target_state))
        try:
            result = self.store.update_state(task_id, target_state, changed_by, reason)
        except (ConflictError, ValidationError) as exc:
            self.ledger_store.append_task_event(
                task_id,
                "state_transition_rejected",
                actor=changed_by,
                trace_id=trace_id,
                run_id=run_id,
                previous_state=previous,
                target_state=target_state_value,
                reason=str(exc),
            )
            raise
        self.ledger_store.append_task_event(
            task_id,
            "state_transitioned",
            actor=changed_by,
            trace_id=trace_id,
            run_id=run_id,
            previous_state=previous,
            target_state=target_state_value,
            reason=reason,
        )
        return result

    def finalize_experience(
        self,
        task_id: str,
        *,
        finalized_by: str,
        trace_id: str | None = None,
        run_id: str | None = None,
    ) -> dict:
        try:
            result = self.store.finalize_experience(task_id=task_id, finalized_by=finalized_by)
        except ConflictError as exc:
            self.ledger_store.append_task_event(
                task_id,
                "writeback_finalize_rejected",
                actor=finalized_by,
                trace_id=trace_id,
                run_id=run_id,
                reason=str(exc),
            )
            raise
        self.ledger_store.append_task_event(
            task_id,
            "writeback_finalized",
            actor=finalized_by,
            trace_id=trace_id,
            run_id=run_id,
            finalization=result.get("finalization", {}),
        )
        return result

    def archive_task(
        self,
        task_id: str,
        *,
        archived_by: str,
        reason: str | None = None,
        trace_id: str | None = None,
        run_id: str | None = None,
    ) -> dict:
        result = self.store.archive_task(task_id, archived_by=archived_by, reason=reason)
        self.ledger_store.append_task_event(
            task_id,
            "task_archived",
            actor=archived_by,
            trace_id=trace_id,
            run_id=run_id,
            reason=reason,
        )
        self.ledger_store.append_audit_event(
            task_id,
            "task_archived",
            actor=archived_by,
            trace_id=trace_id,
            run_id=run_id,
            reason=reason,
        )
        return result

    def task_audit_report(self, task_id: str) -> TaskAuditReport:
        current = None
        try:
            current = self.store.get_task(task_id)
        except NotFoundError:
            current = None
        return TaskAuditReport(
            task_id=task_id,
            current=current,
            events=self.ledger_store.read_task_events(task_id),
        )
