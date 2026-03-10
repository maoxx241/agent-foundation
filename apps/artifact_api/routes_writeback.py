from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from packages.core.observability import record_event, record_metric
from packages.core.storage.fs_utils import ConflictError, NotFoundError, ValidationError

router = APIRouter()


def get_service(request: Request):
    return request.app.state.artifact_service


@router.post("/v1/tasks/{task_id}/experience/finalize")
def finalize_experience(task_id: str, request: Request) -> dict:
    service = get_service(request)
    try:
        result = service.finalize_experience(
            task_id=task_id,
            finalized_by="artifact_api",
            trace_id=request.headers.get("x-trace-id"),
            run_id=request.headers.get("x-run-id"),
        )
        record_event(request, "writeback_finalized", task_id=task_id, state=result["state"])
        record_metric(request, "writeback_finalize_total", 1, task_id=task_id)
        return result
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        record_event(request, "writeback_finalize_rejected", task_id=task_id, reason=str(exc), level="warning")
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
