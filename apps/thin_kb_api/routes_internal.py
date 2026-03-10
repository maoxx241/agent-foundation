from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from packages.core.storage.fs_utils import NotFoundError, ValidationError
from .models import DeprecateObjectRequest, PromoteCandidateRequest

router = APIRouter()


def get_service(request: Request):
    return request.app.state.kb_service


@router.post("/internal/v1/kb/candidates/{candidate_id}/promote")
def promote_candidate(candidate_id: str, payload: PromoteCandidateRequest, request: Request) -> dict:
    service = get_service(request)
    try:
        return service.promote_candidate(
            candidate_id,
            promoted_by=payload.changed_by,
            reason=payload.reason,
            trace_id=request.headers.get("x-trace-id"),
            run_id=request.headers.get("x-run-id"),
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/internal/v1/kb/object/{object_id}/deprecate")
def deprecate_object(object_id: str, payload: DeprecateObjectRequest, request: Request) -> dict:
    service = get_service(request)
    try:
        return service.deprecate_object(
            object_id,
            deprecated_by=payload.changed_by,
            reason=payload.reason,
            superseded_by=payload.superseded_by,
            trace_id=request.headers.get("x-trace-id"),
            run_id=request.headers.get("x-run-id"),
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/internal/v1/audit/object/{object_id}")
def get_object_audit(object_id: str, request: Request) -> dict:
    try:
        return get_service(request).object_audit_report(object_id).model_dump(mode="json")
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
