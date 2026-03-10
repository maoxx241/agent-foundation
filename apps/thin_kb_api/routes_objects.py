from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from packages.core.storage.fs_utils import NotFoundError, ValidationError
from .models import KBSearchRequest

router = APIRouter()


def get_service(request: Request):
    return request.app.state.kb_service


@router.post("/v1/kb/search")
def search_kb(payload: KBSearchRequest, request: Request) -> dict:
    result = get_service(request).search(
        query=payload.query,
        object_types=payload.object_types,
        domain_tags=payload.domain_tags,
        version=payload.version,
        scope=payload.scope,
        status=payload.status,
        limit=payload.limit,
        env_filters=payload.env_filters,
    )
    return result.model_dump(mode="json")


@router.get("/v1/kb/object/{object_id}")
def get_object(object_id: str, request: Request) -> dict:
    try:
        return get_service(request).get(object_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/v1/kb/related/{object_id}")
def get_related(object_id: str, request: Request) -> dict:
    try:
        return get_service(request).related(object_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
