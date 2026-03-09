from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from libs.observability import record_event, record_metric
from libs.storage.fs_utils import NotFoundError, ValidationError
from libs.storage.phase2_store import Phase2Store
from .models import CodeIngestRequest, DocumentIngestRequest, HybridSearchRequest, RefineWritebackRequest

router = APIRouter()


def get_store(request: Request) -> Phase2Store:
    return request.app.state.phase2_store


@router.post("/v1/kb/ingest/document")
def ingest_document(payload: DocumentIngestRequest, request: Request) -> dict:
    store = get_store(request)
    try:
        result = store.ingest_document(payload.model_dump(mode="json"))
    except NotFoundError as exc:
        record_event(request, "document_ingest_failed", reason=str(exc), level="warning")
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        record_event(request, "document_ingest_invalid", reason=str(exc), level="warning")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    record_event(request, "document_ingested", source_id=result.source_id, parser=result.parser)
    record_metric(request, "document_ingest_total", 1)
    return result.model_dump(mode="json")


@router.post("/v1/kb/ingest/code")
def ingest_code(payload: CodeIngestRequest, request: Request) -> dict:
    store = get_store(request)
    try:
        result = store.ingest_code(payload.model_dump(mode="json"))
    except NotFoundError as exc:
        record_event(request, "code_ingest_failed", reason=str(exc), level="warning")
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        record_event(request, "code_ingest_invalid", reason=str(exc), level="warning")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    record_event(request, "code_ingested", source_id=result.source_id, parser=result.parser, language=result.language)
    record_metric(request, "code_ingest_total", 1)
    return result.model_dump(mode="json")


@router.post("/v1/kb/search/hybrid")
def hybrid_search(payload: HybridSearchRequest, request: Request) -> dict:
    store = get_store(request)
    try:
        result = store.search_hybrid(payload.model_dump(mode="json"))
    except ValidationError as exc:
        record_event(request, "kb_search_failed", reason=str(exc), level="warning")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    record_metric(request, "hybrid_search_total", 1, query=payload.query, metric_type="counter")
    return result.model_dump(mode="json")


@router.post("/v1/kb/writeback/refine")
def refine_writeback(payload: RefineWritebackRequest, request: Request) -> dict:
    store = get_store(request)
    try:
        result = store.refine_writeback(payload.model_dump(mode="json"))
    except NotFoundError as exc:
        record_event(request, "kb_publish_failed", task_id=payload.task_id, reason=str(exc), level="warning")
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        record_event(request, "kb_publish_invalid", task_id=payload.task_id, reason=str(exc), level="warning")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    record_event(
        request,
        "kb_publish",
        task_id=result.task_id,
        persisted=result.persisted,
        object_count=len(result.object_ids),
    )
    record_metric(request, "kb_publish_total", 1, task_id=result.task_id)
    record_metric(
        request,
        "kb_promoted_objects_total",
        float(len(result.object_ids)),
        task_id=result.task_id,
    )
    return result.model_dump(mode="json")
