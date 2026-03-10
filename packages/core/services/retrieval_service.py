from __future__ import annotations

from packages.core.schemas import RefinedWriteback
from packages.core.stores.phase2_store import Phase2Store
from .thin_kb_service import ThinKBService


class RetrievalService:
    def __init__(self, phase2_store: Phase2Store, kb_service: ThinKBService):
        self.phase2_store = phase2_store
        self.kb_service = kb_service

    def ingest_document(self, payload: dict):
        return self.phase2_store.ingest_document(payload)

    def ingest_code(self, payload: dict):
        return self.phase2_store.ingest_code(payload)

    def search_hybrid(self, payload: dict):
        return self.phase2_store.search_hybrid(payload)

    def refine_writeback(
        self,
        payload: dict,
        *,
        actor: str,
        trace_id: str | None = None,
        run_id: str | None = None,
    ) -> RefinedWriteback:
        requested_persist = bool(payload.get("persist", False))
        draft = self.phase2_store.refine_writeback({**payload, "persist": False})
        if not requested_persist:
            return draft

        persisted_objects = []
        object_ids: list[str] = []
        for item in draft.objects:
            candidate = self.kb_service.create_candidate(item, actor=actor, trace_id=trace_id, run_id=run_id)
            persisted_objects.append(candidate)
            object_ids.append(candidate["id"])

        return RefinedWriteback(
            task_id=draft.task_id,
            persisted=True,
            persist_target="candidate",
            object_status="candidate",
            summary=f"Refined {len(persisted_objects)} candidate object(s) from task {draft.task_id}",
            object_ids=object_ids,
            objects=persisted_objects,
            warnings=draft.warnings,
            created_at=draft.created_at,
            updated_at=draft.updated_at,
        )
