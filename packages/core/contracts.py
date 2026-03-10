from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from apps.artifact_api.main import create_app as create_artifact_app
from apps.thin_kb_api.main import create_app as create_kb_app
from packages.core.events import LedgerEvent, ObjectAuditReport, TaskAuditReport
from packages.core.schemas import (
    ADR,
    Case,
    Claim,
    Decision,
    DesignReview,
    DesignSpec,
    EvidencePack,
    ExperiencePacket,
    ExtractBundle,
    ExtractedChunk,
    HybridSearchHit,
    HybridSearchResponse,
    ImplReview,
    Procedure,
    RefinedWriteback,
    SearchHit,
    SearchResponse,
    SelfTestReport,
    SourceRecord,
    TaskBrief,
    TaskStateRecord,
    TestSpec,
    ValidationReport,
)
from packages.core.storage.artifact_store import ArtifactStore
from packages.core.storage.phase2_store import Phase2Store
from packages.core.storage.thin_kb_store import ThinKBStore


def build_openapi_contracts() -> dict[str, dict[str, Any]]:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        artifact_app = create_artifact_app(ArtifactStore(root / "tasks"))
        kb_store = ThinKBStore(root / "kb", root / "indexes" / "sqlite" / "manifest.sqlite3")
        phase2_store = Phase2Store(
            kb_root=kb_store.kb_root,
            db_path=kb_store.db_path,
            tasks_root=root / "tasks",
            canonical_store=kb_store,
            lancedb_root=root / "indexes" / "lancedb",
        )
        thin_kb_app = create_kb_app(kb_store, phase2_store)
        return {
            "artifact_api.v1.json": artifact_app.openapi(),
            "thin_kb_api.v1.json": thin_kb_app.openapi(),
        }


def build_jsonschema_contracts() -> dict[str, dict[str, Any]]:
    return {
        "artifact_models.v1.json": _bundle(
            "artifact_models.v1",
            [
                TaskBrief,
                TaskStateRecord,
                EvidencePack,
                DesignSpec,
                DesignReview,
                TestSpec,
                SelfTestReport,
                ImplReview,
                ValidationReport,
                ADR,
                ExperiencePacket,
            ],
        ),
        "thin_kb_models.v1.json": _bundle(
            "thin_kb_models.v1",
            [
                Claim,
                Procedure,
                Case,
                Decision,
                SearchHit,
                SearchResponse,
            ],
        ),
        "phase2_models.v1.json": _bundle(
            "phase2_models.v1",
            [
                SourceRecord,
                ExtractedChunk,
                ExtractBundle,
                HybridSearchHit,
                HybridSearchResponse,
                RefinedWriteback,
            ],
        ),
        "event_models.v1.json": _bundle(
            "event_models.v1",
            [
                LedgerEvent,
                TaskAuditReport,
                ObjectAuditReport,
            ],
        ),
    }


def _bundle(name: str, models: list[type]) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "bundle": name,
        "models": {model.__name__: model.model_json_schema() for model in models},
    }
