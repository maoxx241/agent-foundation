from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI

from packages.core.config import (
    ensure_runtime_layout,
    kb_db_path,
    kb_root,
    lancedb_indexes_root,
    lancedb_sync_enabled,
    ledgers_root,
    observability_root,
    phase2_allowed_source_roots,
    tasks_root,
    validate_runtime_roots,
    validate_service_tokens,
)
from packages.core.observability import Observability, install_observability
from packages.core.security import default_service_auth, install_auth, require_agent_access, require_operator_access
from packages.core.services.retrieval_service import RetrievalService
from packages.core.services.thin_kb_service import ThinKBService
from packages.core.services.writeback_service import WritebackService
from packages.core.stores.ledger_store import LedgerStore
from packages.core.storage.phase2_store import Phase2Store
from packages.core.storage.thin_kb_store import ThinKBStore
from .routes_cases import router as cases_router
from .routes_claims import router as claims_router
from .routes_decisions import router as decisions_router
from .routes_internal import router as internal_router
from .routes_objects import router as objects_router
from .routes_phase2 import router as phase2_router
from .routes_procedures import router as procedures_router


def _default_kb_paths() -> tuple[Path, Path]:
    return kb_root(), kb_db_path()


def _default_tasks_root() -> Path:
    return tasks_root()


def _default_observability_root() -> Path:
    return observability_root()


def _default_ledger_root() -> Path:
    return ledgers_root()


def create_app(
    store: Optional[ThinKBStore] = None,
    phase2_store: Optional[Phase2Store] = None,
    observability: Optional[Observability] = None,
    ledger_store: Optional[LedgerStore] = None,
) -> FastAPI:
    app = FastAPI(title="agent-foundation Thin KB API", version="0.1.0")
    using_default_store = store is None
    if store is None:
        validate_runtime_roots()
        ensure_runtime_layout()
        kb_root, db_path = _default_kb_paths()
        store = ThinKBStore(kb_root=kb_root, db_path=db_path)
    if phase2_store is None:
        state_parent = store.kb_root.parent
        phase2_store = Phase2Store(
            kb_root=store.kb_root,
            db_path=store.db_path,
            tasks_root=_default_tasks_root() if using_default_store else state_parent / "tasks",
            canonical_store=store,
            lancedb_root=lancedb_indexes_root() if using_default_store else state_parent / "indexes" / "lancedb",
            allowed_source_roots=phase2_allowed_source_roots() if using_default_store else (),
            enable_lancedb_sync=lancedb_sync_enabled(),
        )
    if observability is None:
        root = _default_observability_root() if using_default_store else store.kb_root.parent / "observability"
        observability = Observability(root / "thin_kb_api")
    if ledger_store is None:
        root = _default_ledger_root() if using_default_store else store.kb_root.parent / "ledgers"
        ledger_store = LedgerStore(root)
    kb_service = ThinKBService(store, ledger_store)
    retrieval_service = RetrievalService(phase2_store, kb_service)
    writeback_service = WritebackService(kb_service)
    install_auth(app, default_service_auth(allow_insecure_defaults=True))
    install_observability(app, observability)
    app.state.kb_store = store
    app.state.phase2_store = phase2_store
    app.state.ledger_store = ledger_store
    app.state.kb_service = kb_service
    app.state.retrieval_service = retrieval_service
    app.state.writeback_service = writeback_service
    agent_dependencies = [Depends(require_agent_access)]
    operator_dependencies = [Depends(require_operator_access)]
    app.include_router(claims_router, dependencies=agent_dependencies)
    app.include_router(procedures_router, dependencies=agent_dependencies)
    app.include_router(cases_router, dependencies=agent_dependencies)
    app.include_router(decisions_router, dependencies=agent_dependencies)
    app.include_router(objects_router, dependencies=agent_dependencies)
    app.include_router(phase2_router, dependencies=agent_dependencies)
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
