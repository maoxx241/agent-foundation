from __future__ import annotations

from packages.core.events import ObjectAuditReport
from packages.core.stores.kb_store import ThinKBStore
from packages.core.stores.ledger_store import LedgerStore
from packages.core.storage.fs_utils import NotFoundError


class ThinKBService:
    def __init__(self, store: ThinKBStore, ledger_store: LedgerStore):
        self.store = store
        self.ledger_store = ledger_store

    def search(self, **kwargs):
        return self.store.search(**kwargs)

    def get(self, object_id: str) -> dict:
        return self.store.get(object_id)

    def related(self, object_id: str) -> dict:
        return self.store.related(object_id)

    def create_candidate(
        self,
        payload: dict,
        *,
        actor: str,
        trace_id: str | None = None,
        run_id: str | None = None,
    ) -> dict:
        result = self.store.create_candidate(payload)
        self.ledger_store.append_kb_event(
            result["id"],
            "candidate_created",
            actor=actor,
            trace_id=trace_id,
            run_id=run_id,
            object_type=result["object_type"],
            status=result["status"],
        )
        return result

    def promote_candidate(
        self,
        candidate_id: str,
        *,
        promoted_by: str,
        reason: str | None = None,
        trace_id: str | None = None,
        run_id: str | None = None,
    ) -> dict:
        result = self.store.promote_candidate(candidate_id, promoted_by=promoted_by, reason=reason)
        self.ledger_store.append_kb_event(
            candidate_id,
            "candidate_promoted",
            actor=promoted_by,
            trace_id=trace_id,
            run_id=run_id,
            reason=reason,
            promoted_status=result["status"],
        )
        self.ledger_store.append_audit_event(
            candidate_id,
            "candidate_promoted",
            actor=promoted_by,
            trace_id=trace_id,
            run_id=run_id,
            reason=reason,
        )
        return result

    def deprecate_object(
        self,
        object_id: str,
        *,
        deprecated_by: str,
        reason: str,
        superseded_by: str | None = None,
        trace_id: str | None = None,
        run_id: str | None = None,
    ) -> dict:
        result = self.store.deprecate_object(
            object_id,
            deprecated_by=deprecated_by,
            reason=reason,
            superseded_by=superseded_by,
        )
        self.ledger_store.append_kb_event(
            object_id,
            "object_deprecated",
            actor=deprecated_by,
            trace_id=trace_id,
            run_id=run_id,
            reason=reason,
            superseded_by=superseded_by,
        )
        if superseded_by:
            self.ledger_store.append_kb_event(
                object_id,
                "object_superseded",
                actor=deprecated_by,
                trace_id=trace_id,
                run_id=run_id,
                superseded_by=superseded_by,
            )
        self.ledger_store.append_audit_event(
            object_id,
            "object_deprecated",
            actor=deprecated_by,
            trace_id=trace_id,
            run_id=run_id,
            reason=reason,
            superseded_by=superseded_by,
        )
        return result

    def object_audit_report(self, object_id: str) -> ObjectAuditReport:
        current = None
        try:
            current = self.store.get(object_id)
        except NotFoundError:
            current = None
        return ObjectAuditReport(
            object_id=object_id,
            current=current,
            events=self.ledger_store.read_kb_events(object_id),
        )
