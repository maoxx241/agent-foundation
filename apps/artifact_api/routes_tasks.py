from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from libs.observability import record_event, record_metric
from libs.storage.artifact_store import ArtifactStore
from libs.storage.fs_utils import ConflictError, NotFoundError, ValidationError
from .models import CreateTaskRequest, UpdateTaskStateRequest

router = APIRouter()


def get_store(request: Request) -> ArtifactStore:
    return request.app.state.artifact_store


@router.post("/v1/tasks")
def create_task(payload: CreateTaskRequest, request: Request) -> dict:
    store = get_store(request)
    try:
        result = store.create_task(payload.model_dump(mode="json"))
        record_event(request, "task_created", task_id=payload.task_id, project_id=payload.project_id)
        record_metric(request, "task_created_total", 1, task_id=payload.task_id)
        return result
    except ConflictError as exc:
        record_event(request, "task_create_rejected", task_id=payload.task_id, reason=str(exc), level="warning")
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        record_event(request, "task_create_invalid", task_id=payload.task_id, reason=str(exc), level="warning")
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/v1/tasks/{task_id}")
def get_task(task_id: str, request: Request) -> dict:
    store = get_store(request)
    try:
        return store.get_task(task_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/v1/tasks/{task_id}/state")
def update_task_state(task_id: str, payload: UpdateTaskStateRequest, request: Request) -> dict:
    store = get_store(request)
    try:
        previous = store.get_state(task_id)["state"]
        result = store.update_state(
            task_id=task_id,
            target_state=payload.target_state,
            changed_by=payload.changed_by,
            reason=payload.reason,
        )
        record_event(
            request,
            "task_state_updated",
            task_id=task_id,
            previous_state=previous,
            target_state=payload.target_state,
            changed_by=payload.changed_by,
        )
        record_metric(request, "task_state_update_total", 1, task_id=task_id, target_state=payload.target_state)
        return result
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        record_event(
            request,
            "task_state_update_rejected",
            task_id=task_id,
            target_state=payload.target_state,
            changed_by=payload.changed_by,
            reason=str(exc),
            level="warning",
        )
        if str(payload.target_state) == "VALIDATED":
            record_metric(request, "validation_failures_total", 1, task_id=task_id, target_state=payload.target_state)
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/v1/tasks/{task_id}/bundle")
def get_task_bundle(task_id: str, request: Request) -> dict:
    store = get_store(request)
    try:
        return store.bundle_task(task_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
