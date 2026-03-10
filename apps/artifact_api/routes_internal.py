from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from packages.core.storage.fs_utils import ConflictError, NotFoundError, ValidationError
from .models import ArchiveTaskRequest

router = APIRouter()


def get_service(request: Request):
    return request.app.state.artifact_service


@router.post("/internal/v1/tasks/{task_id}/archive")
def archive_task(task_id: str, payload: ArchiveTaskRequest, request: Request) -> dict:
    service = get_service(request)
    try:
        return service.archive_task(
            task_id,
            archived_by=payload.changed_by,
            reason=payload.reason,
            trace_id=request.headers.get("x-trace-id"),
            run_id=request.headers.get("x-run-id"),
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/internal/v1/audit/task/{task_id}")
def get_task_audit(task_id: str, request: Request) -> dict:
    try:
        return get_service(request).task_audit_report(task_id).model_dump(mode="json")
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
