from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI

from libs.observability import Observability, install_observability
from libs.storage.artifact_store import ArtifactStore
from .routes_artifacts import router as artifacts_router
from .routes_tasks import router as tasks_router
from .routes_writeback import router as writeback_router


def _default_tasks_root() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    return Path(os.getenv("AGENT_FOUNDATION_TASKS_ROOT", repo_root / "tasks"))


def _default_observability_root() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    return Path(os.getenv("AGENT_FOUNDATION_OBSERVABILITY_ROOT", repo_root / "observability"))


def create_app(store: Optional[ArtifactStore] = None, observability: Optional[Observability] = None) -> FastAPI:
    app = FastAPI(title="agent-foundation Artifact API", version="0.1.0")
    app.state.artifact_store = store or ArtifactStore(_default_tasks_root())
    install_observability(app, observability or Observability(_default_observability_root() / "artifact_api"))
    app.include_router(tasks_router)
    app.include_router(artifacts_router)
    app.include_router(writeback_router)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
