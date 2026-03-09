from __future__ import annotations

import json
import uuid
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Any, Optional

from fastapi import FastAPI, Request

from libs.storage.fs_utils import ensure_dir, utc_now


class Observability:
    def __init__(self, root: Path):
        self.root = root
        ensure_dir(self.root)
        self.events_path = self.root / "events.jsonl"
        self.metrics_path = self.root / "metrics.jsonl"

    def emit_event(
        self,
        name: str,
        *,
        trace_id: Optional[str] = None,
        run_id: Optional[str] = None,
        task_id: Optional[str] = None,
        level: str = "info",
        **fields: Any,
    ) -> None:
        payload = {
            "timestamp": utc_now().isoformat(),
            "kind": "event",
            "name": name,
            "level": level,
            "trace_id": trace_id,
            "run_id": run_id,
            "task_id": task_id,
            **fields,
        }
        _append_jsonl(self.events_path, payload)

    def emit_metric(
        self,
        name: str,
        value: float,
        *,
        trace_id: Optional[str] = None,
        run_id: Optional[str] = None,
        task_id: Optional[str] = None,
        metric_type: str = "counter",
        **fields: Any,
    ) -> None:
        payload = {
            "timestamp": utc_now().isoformat(),
            "kind": "metric",
            "name": name,
            "metric_type": metric_type,
            "value": value,
            "trace_id": trace_id,
            "run_id": run_id,
            "task_id": task_id,
            **fields,
        }
        _append_jsonl(self.metrics_path, payload)


def install_observability(app: FastAPI, observability: Observability) -> None:
    app.state.observability = observability

    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        trace_id = request.headers.get("x-trace-id") or str(uuid.uuid4())
        run_id = request.headers.get("x-run-id")
        request.state.trace_id = trace_id
        request.state.run_id = run_id
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            latency_ms = int((perf_counter() - started) * 1000)
            observability.emit_event(
                "request_failed",
                trace_id=trace_id,
                run_id=run_id,
                task_id=task_id_from_request(request),
                path=request.url.path,
                method=request.method,
                error_type=type(exc).__name__,
                latency_ms=latency_ms,
                level="error",
            )
            observability.emit_metric(
                "http_request_total",
                1,
                trace_id=trace_id,
                run_id=run_id,
                task_id=task_id_from_request(request),
                method=request.method,
                path=request.url.path,
                status_code=500,
            )
            observability.emit_metric(
                "http_latency_ms",
                latency_ms,
                trace_id=trace_id,
                run_id=run_id,
                task_id=task_id_from_request(request),
                metric_type="timing",
                method=request.method,
                path=request.url.path,
                status_code=500,
            )
            raise

        latency_ms = int((perf_counter() - started) * 1000)
        response.headers["x-trace-id"] = trace_id
        if run_id:
            response.headers["x-run-id"] = run_id
        observability.emit_event(
            "request_completed",
            trace_id=trace_id,
            run_id=run_id,
            task_id=task_id_from_request(request),
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
            latency_ms=latency_ms,
        )
        observability.emit_metric(
            "http_request_total",
            1,
            trace_id=trace_id,
            run_id=run_id,
            task_id=task_id_from_request(request),
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )
        observability.emit_metric(
            "http_latency_ms",
            latency_ms,
            trace_id=trace_id,
            run_id=run_id,
            task_id=task_id_from_request(request),
            metric_type="timing",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )
        return response


def record_event(request: Request, name: str, *, task_id: Optional[str] = None, **fields: Any) -> None:
    observability: Observability = request.app.state.observability
    observability.emit_event(
        name,
        trace_id=trace_id_from_request(request),
        run_id=run_id_from_request(request),
        task_id=task_id or task_id_from_request(request),
        **fields,
    )


def record_metric(
    request: Request,
    name: str,
    value: float,
    *,
    task_id: Optional[str] = None,
    metric_type: str = "counter",
    **fields: Any,
) -> None:
    observability: Observability = request.app.state.observability
    observability.emit_metric(
        name,
        value,
        trace_id=trace_id_from_request(request),
        run_id=run_id_from_request(request),
        task_id=task_id or task_id_from_request(request),
        metric_type=metric_type,
        **fields,
    )


def trace_id_from_request(request: Request) -> Optional[str]:
    return getattr(request.state, "trace_id", None) or request.headers.get("x-trace-id")


def run_id_from_request(request: Request) -> Optional[str]:
    return getattr(request.state, "run_id", None) or request.headers.get("x-run-id")


def task_id_from_request(request: Request) -> Optional[str]:
    return request.path_params.get("task_id")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records.append(json.loads(line))
    return records


def build_metrics_report(root: Path) -> dict[str, Any]:
    observability = Observability(root)
    events = load_jsonl(observability.events_path)
    metrics = load_jsonl(observability.metrics_path)
    request_metrics = [item for item in metrics if item["name"] == "http_request_total"]
    latency_metrics = [item for item in metrics if item["name"] == "http_latency_ms"]
    retrieval_latencies = [
        item["value"]
        for item in latency_metrics
        if "/v1/kb/" in str(item.get("path", "")) and "search" in str(item.get("path", ""))
    ]
    validation_attempts = [
        item
        for item in events
        if item["name"] in {"task_state_updated", "task_state_update_rejected"} and item.get("target_state") == "VALIDATED"
    ]
    validation_failures = [item for item in validation_attempts if item["name"] == "task_state_update_rejected"]
    promotion_events = [item for item in events if item["name"] == "kb_publish"]
    intervention_events = [item for item in events if item["name"] == "human_intervention"]

    return {
        "generated_at": utc_now().isoformat(),
        "requests_total": len(request_metrics),
        "errors_total": len([item for item in request_metrics if int(item.get("status_code", 200)) >= 400]),
        "retrieval_latency_ms": _latency_summary(retrieval_latencies),
        "validation_fail_rate": _rate(len(validation_failures), len(validation_attempts)),
        "writeback_promotion_rate": _rate(
            len([item for item in promotion_events if int(item.get("object_count", 0)) > 0]),
            len(promotion_events),
        ),
        "human_intervention_rate": _rate(len(intervention_events), len(request_metrics)),
    }


def _latency_summary(values: list[float]) -> dict[str, float]:
    if not values:
        return {"count": 0, "avg": 0.0, "p95": 0.0}
    ordered = sorted(values)
    p95_index = min(int(len(ordered) * 0.95), len(ordered) - 1)
    return {
        "count": float(len(values)),
        "avg": round(mean(values), 3),
        "p95": round(float(ordered[p95_index]), 3),
    }


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n")
