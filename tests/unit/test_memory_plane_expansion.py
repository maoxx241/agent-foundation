from __future__ import annotations

from packages.core.integrations.memory_plane import MemoryBackendError, MemoryPlane


class RecordingBackend:
    def __init__(self):
        self.calls = []

    def search(self, scope: str, query: str, limit: int = 5):
        self.calls.append(("search", scope, query, limit))
        return [{"id": "mem-1", "scope": scope, "query": query}]

    def store(self, scope: str, payload):
        self.calls.append(("store", scope, payload))
        return {"id": "mem-1", "scope": scope, "payload": payload}


class BrokenBackend:
    def search(self, scope: str, query: str, limit: int = 5):
        raise MemoryBackendError("semantic index unavailable")

    def store(self, scope: str, payload):
        raise MemoryBackendError("semantic index unavailable")


def test_m04_scope_is_forwarded_without_cross_leak():
    backend = RecordingBackend()
    plane = MemoryPlane(backend, slow_threshold_ms=100)

    recall = plane.recall(scope="project", query="retrieval")
    capture = plane.capture(scope="session", payload={"fact": "remember this"}, mode="auto")

    assert recall["hits"][0]["scope"] == "project"
    assert capture["record"]["scope"] == "session"
    assert backend.calls[0] == ("search", "project", "retrieval", 5)
    assert backend.calls[1] == ("store", "session", {"fact": "remember this"})


def test_m09_duplicate_store_is_stable_when_backend_is_stable():
    backend = RecordingBackend()
    plane = MemoryPlane(backend, slow_threshold_ms=100)

    first = plane.capture(scope="user", payload={"fact": "prefers concise"}, mode="auto")
    second = plane.capture(scope="user", payload={"fact": "prefers concise"}, mode="auto")

    assert first["record"]["id"] == second["record"]["id"] == "mem-1"


def test_m10_backend_conflict_is_explicit_for_manual_and_auto_modes():
    plane = MemoryPlane(BrokenBackend(), slow_threshold_ms=100)

    manual = plane.capture(scope="user", payload={"fact": "manual"}, mode="manual")
    auto = plane.capture(scope="user", payload={"fact": "auto"}, mode="auto")

    assert manual["ok"] is False
    assert manual["degraded"] is False
    assert "semantic index unavailable" in manual["warnings"][0]
    assert auto["ok"] is False
    assert auto["degraded"] is True
