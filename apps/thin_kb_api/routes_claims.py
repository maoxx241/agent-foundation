from __future__ import annotations

from fastapi import APIRouter, Request

from .models import KBSearchRequest

router = APIRouter()


def get_service(request: Request):
    return request.app.state.kb_service


@router.post("/v1/kb/claims/search")
def search_claims(payload: KBSearchRequest, request: Request) -> dict:
    result = get_service(request).search(
        query=payload.query,
        object_types=["claim"],
        domain_tags=payload.domain_tags,
        version=payload.version,
        scope=payload.scope,
        status=payload.status,
        limit=payload.limit,
    )
    return result.model_dump(mode="json")
