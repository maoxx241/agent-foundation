from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from libs.storage.fs_utils import NotFoundError
from libs.storage.thin_kb_store import ThinKBStore
from .models import KBSearchRequest

router = APIRouter()


def get_store(request: Request) -> ThinKBStore:
    return request.app.state.kb_store


@router.post("/v1/kb/search")
def search_kb(payload: KBSearchRequest, request: Request) -> dict:
    store = get_store(request)
    result = store.search(
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
    store = get_store(request)
    try:
        return store.get(object_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/v1/kb/related/{object_id}")
def get_related(object_id: str, request: Request) -> dict:
    store = get_store(request)
    try:
        return store.related(object_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
