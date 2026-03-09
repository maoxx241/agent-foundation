from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from libs.observability import record_event, record_metric
from libs.storage.artifact_store import ArtifactStore
from libs.storage.fs_utils import ConflictError, NotFoundError

router = APIRouter()


def get_store(request: Request) -> ArtifactStore:
    return request.app.state.artifact_store


@router.post("/v1/tasks/{task_id}/experience/finalize")
def finalize_experience(task_id: str, request: Request) -> dict:
    store = get_store(request)
    try:
        result = store.finalize_experience(task_id=task_id, finalized_by="artifact_api")
        record_event(request, "writeback_finalized", task_id=task_id, state=result["state"])
        record_metric(request, "writeback_finalize_total", 1, task_id=task_id)
        return result
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        record_event(request, "writeback_finalize_rejected", task_id=task_id, reason=str(exc), level="warning")
        raise HTTPException(status_code=409, detail=str(exc)) from exc
