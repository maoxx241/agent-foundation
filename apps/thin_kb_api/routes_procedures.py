from __future__ import annotations

from fastapi import APIRouter, Request

from libs.storage.thin_kb_store import ThinKBStore
from .models import KBSearchRequest

router = APIRouter()


def get_store(request: Request) -> ThinKBStore:
    return request.app.state.kb_store


@router.post("/v1/kb/procedures/search")
def search_procedures(payload: KBSearchRequest, request: Request) -> dict:
    store = get_store(request)
    result = store.search(
        query=payload.query,
        object_types=["procedure"],
        domain_tags=payload.domain_tags,
        version=payload.version,
        scope=payload.scope,
        status=payload.status,
        limit=payload.limit,
    )
    return result.model_dump(mode="json")
