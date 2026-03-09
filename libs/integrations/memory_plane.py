from __future__ import annotations

import time
from typing import Any, Dict, List, Protocol


class MemoryBackendError(Exception):
    """Base error for a memory backend call."""


class MemoryBackendUnavailable(MemoryBackendError):
    """Raised when the memory backend cannot serve requests."""


class MemoryBackend(Protocol):
    def search(self, scope: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        ...

    def store(self, scope: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...


class MemoryPlane:
    """Thin wrapper that normalizes healthy, slow, and unavailable memory backends."""

    def __init__(self, backend: MemoryBackend, slow_threshold_ms: int = 250):
        self.backend = backend
        self.slow_threshold_ms = slow_threshold_ms

    def recall(self, scope: str, query: str, limit: int = 5) -> Dict[str, Any]:
        started = time.perf_counter()
        try:
            hits = self.backend.search(scope=scope, query=query, limit=limit)
            elapsed_ms = self._elapsed_ms(started)
            warnings = []
            if elapsed_ms >= self.slow_threshold_ms:
                warnings.append(f"memory backend slow: {elapsed_ms}ms")
            return {
                "ok": True,
                "degraded": False,
                "scope": scope,
                "query": query,
                "hits": hits,
                "warnings": warnings,
                "latency_ms": elapsed_ms,
            }
        except MemoryBackendUnavailable as exc:
            return {
                "ok": False,
                "degraded": True,
                "scope": scope,
                "query": query,
                "hits": [],
                "warnings": [str(exc)],
                "latency_ms": self._elapsed_ms(started),
            }

    def capture(self, scope: str, payload: Dict[str, Any], mode: str = "auto") -> Dict[str, Any]:
        started = time.perf_counter()
        try:
            stored = self.backend.store(scope=scope, payload=payload)
            elapsed_ms = self._elapsed_ms(started)
            warnings = []
            if elapsed_ms >= self.slow_threshold_ms:
                warnings.append(f"memory backend slow: {elapsed_ms}ms")
            return {
                "ok": True,
                "degraded": False,
                "scope": scope,
                "mode": mode,
                "record": stored,
                "warnings": warnings,
                "latency_ms": elapsed_ms,
            }
        except MemoryBackendUnavailable as exc:
            return {
                "ok": False,
                "degraded": True,
                "scope": scope,
                "mode": mode,
                "record": None,
                "warnings": [str(exc)],
                "latency_ms": self._elapsed_ms(started),
            }
        except MemoryBackendError as exc:
            return {
                "ok": False,
                "degraded": mode == "auto",
                "scope": scope,
                "mode": mode,
                "record": None,
                "warnings": [str(exc)],
                "latency_ms": self._elapsed_ms(started),
            }

    def _elapsed_ms(self, started: float) -> int:
        return int((time.perf_counter() - started) * 1000)
