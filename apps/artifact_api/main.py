from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI

from packages.core.config import (
    ensure_runtime_layout,
    ledgers_root,
    observability_root,
    tasks_root,
    validate_runtime_roots,
    validate_service_tokens,
)
from packages.core.observability import Observability, install_observability
from packages.core.security import default_service_auth, install_auth, require_agent_access, require_operator_access
from packages.core.services.artifact_service import ArtifactService
from packages.core.stores.ledger_store import LedgerStore
from packages.core.storage.artifact_store import ArtifactStore
from .routes_artifacts import router as artifacts_router
from .routes_internal import router as internal_router
from .routes_tasks import router as tasks_router
from .routes_writeback import router as writeback_router


def _default_tasks_root() -> Path:
    return tasks_root()


def _default_observability_root() -> Path:
    return observability_root()


def _default_ledger_root() -> Path:
    return ledgers_root()


def create_app(
    store: Optional[ArtifactStore] = None,
    observability: Optional[Observability] = None,
    ledger_store: Optional[LedgerStore] = None,
) -> FastAPI:
    app = FastAPI(title="agent-foundation Artifact API", version="0.1.0")
    using_default_store = store is None
    if store is None:
        validate_runtime_roots()
        ensure_runtime_layout()
        store = ArtifactStore(_default_tasks_root())
    if observability is None:
        root = _default_observability_root() if using_default_store else store.tasks_root.parent / "observability"
        observability = Observability(root / "artifact_api")
    if ledger_store is None:
        root = _default_ledger_root() if using_default_store else store.tasks_root.parent / "ledgers"
        ledger_store = LedgerStore(root)

    install_auth(app, default_service_auth(allow_insecure_defaults=True))
    install_observability(app, observability)
    app.state.artifact_store = store
    app.state.ledger_store = ledger_store
    app.state.artifact_service = ArtifactService(store, ledger_store)
    agent_dependencies = [Depends(require_agent_access)]
    operator_dependencies = [Depends(require_operator_access)]
    app.include_router(tasks_router, dependencies=agent_dependencies)
    app.include_router(artifacts_router, dependencies=agent_dependencies)
    app.include_router(writeback_router, dependencies=agent_dependencies)
    app.include_router(internal_router, dependencies=operator_dependencies)

    if using_default_store:

        @app.on_event("startup")
        async def validate_runtime_startup() -> None:
            validate_service_tokens()

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz() -> dict[str, str]:
        return {"status": "ready"}

    return app


app = create_app()
