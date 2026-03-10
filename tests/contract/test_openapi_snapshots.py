from __future__ import annotations

import json
from pathlib import Path

from apps.artifact_api.main import create_app as create_artifact_app
from apps.thin_kb_api.main import create_app as create_kb_app
from packages.core.storage.artifact_store import ArtifactStore
from packages.core.storage.phase2_store import Phase2Store
from packages.core.storage.thin_kb_store import ThinKBStore


def _snapshot_root() -> Path:
    return Path(__file__).resolve().parents[2] / "contracts" / "openapi"


def test_artifact_openapi_snapshot_matches_runtime(tmp_path):
    app = create_artifact_app(ArtifactStore(tmp_path / "tasks"))
    expected = json.loads((_snapshot_root() / "artifact_api.v1.json").read_text(encoding="utf-8"))
    assert app.openapi() == expected


def test_thin_kb_openapi_snapshot_matches_runtime(tmp_path):
    kb_root = tmp_path / "kb"
    store = ThinKBStore(kb_root, kb_root / "manifest.sqlite3")
    phase2 = Phase2Store(kb_root=kb_root, db_path=store.db_path, tasks_root=tmp_path / "tasks", canonical_store=store)
    app = create_kb_app(store, phase2)
    expected = json.loads((_snapshot_root() / "thin_kb_api.v1.json").read_text(encoding="utf-8"))
    assert app.openapi() == expected
