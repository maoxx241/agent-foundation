from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from packages.core.storage.fs_utils import NotFoundError, ValidationError
from .models import PutArtifactRequest

router = APIRouter()


def get_service(request: Request):
    return request.app.state.artifact_service


@router.get("/v1/tasks/{task_id}/artifacts")
def list_artifacts(task_id: str, request: Request) -> dict:
    try:
        return {
            "task_id": task_id,
            "artifacts": get_service(request).list_artifacts(task_id),
        }
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/v1/tasks/{task_id}/artifacts/{stage}/{name}")
def get_artifact(task_id: str, stage: str, name: str, request: Request) -> dict:
    try:
        return get_service(request).get_artifact(task_id, stage, name)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/v1/tasks/{task_id}/artifacts/{stage}/{name}")
def put_artifact(task_id: str, stage: str, name: str, payload: PutArtifactRequest, request: Request) -> dict:
    try:
        return get_service(request).put_artifact(
            task_id=task_id,
            stage=stage,
            name=name,
            payload_format=payload.format,
            content=payload.content,
            actor="artifact_api",
            trace_id=request.headers.get("x-trace-id"),
            run_id=request.headers.get("x-run-id"),
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
