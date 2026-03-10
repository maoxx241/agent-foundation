from __future__ import annotations

import time

from packages.core.integrations.memory_plane import MemoryBackendUnavailable, MemoryPlane


class HealthyBackend:
    def search(self, scope: str, query: str, limit: int = 5):
        return []

    def store(self, scope: str, payload):
        return {"id": "mem-1", "scope": scope, "payload": payload}


class SlowBackend:
    def __init__(self, delay_s: float = 0.02):
        self.delay_s = delay_s

    def search(self, scope: str, query: str, limit: int = 5):
        time.sleep(self.delay_s)
        return [{"id": "mem-hit", "scope": scope}]

    def store(self, scope: str, payload):
        time.sleep(self.delay_s)
        return {"id": "mem-2", "scope": scope}


class UnavailableBackend:
    def search(self, scope: str, query: str, limit: int = 5):
        raise MemoryBackendUnavailable("backend unavailable")

    def store(self, scope: str, payload):
        raise MemoryBackendUnavailable("backend unavailable")


def test_m01_healthy_no_hit_and_store_success():
    plane = MemoryPlane(HealthyBackend(), slow_threshold_ms=100)
    recall = plane.recall(scope="user", query="missing")
    capture = plane.capture(scope="user", payload={"fact": "prefers concise"}, mode="auto")

    assert recall["ok"] is True
    assert recall["hits"] == []
    assert capture["ok"] is True
    assert capture["record"]["id"] == "mem-1"


def test_m02_slow_backend_surfaces_warning_and_manual_store():
    plane = MemoryPlane(SlowBackend(), slow_threshold_ms=1)
    recall = plane.recall(scope="project", query="runtime")
    capture = plane.capture(scope="project", payload={"fact": "shared runtime"}, mode="manual")

    assert recall["ok"] is True
    assert recall["hits"][0]["id"] == "mem-hit"
    assert recall["warnings"]
    assert capture["ok"] is True
    assert capture["warnings"]


def test_m03_unavailable_backend_degrades_gracefully():
    plane = MemoryPlane(UnavailableBackend(), slow_threshold_ms=100)
    recall = plane.recall(scope="task", query="recent context")
    capture = plane.capture(scope="task", payload={"fact": "latest context"}, mode="auto")

    assert recall["ok"] is False
    assert recall["degraded"] is True
    assert "backend unavailable" in recall["warnings"][0]
    assert capture["ok"] is False
    assert capture["degraded"] is True
