from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from packages.core.observability import record_event, record_metric
from packages.core.storage.fs_utils import NotFoundError, ValidationError
from .models import CodeIngestRequest, DocumentIngestRequest, HybridSearchRequest, RefineWritebackRequest

router = APIRouter()


def get_service(request: Request):
    return request.app.state.retrieval_service


@router.post("/v1/kb/ingest/document")
def ingest_document(payload: DocumentIngestRequest, request: Request) -> dict:
    service = get_service(request)
    try:
        result = service.ingest_document(payload.model_dump(mode="json"))
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
    service = get_service(request)
    try:
        result = service.ingest_code(payload.model_dump(mode="json"))
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
    try:
        result = get_service(request).search_hybrid(payload.model_dump(mode="json"))
    except ValidationError as exc:
        record_event(request, "kb_search_failed", reason=str(exc), level="warning")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    record_metric(request, "hybrid_search_total", 1, query=payload.query, metric_type="counter")
    return result.model_dump(mode="json")


@router.post("/v1/kb/writeback/refine")
def refine_writeback(payload: RefineWritebackRequest, request: Request) -> dict:
    service = get_service(request)
    try:
        result = service.refine_writeback(
            payload.model_dump(mode="json"),
            actor="thin_kb_api",
            trace_id=request.headers.get("x-trace-id"),
            run_id=request.headers.get("x-run-id"),
        )
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
