from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI

from libs.observability import Observability, install_observability
from libs.storage.phase2_store import Phase2Store
from libs.storage.thin_kb_store import ThinKBStore
from .routes_cases import router as cases_router
from .routes_claims import router as claims_router
from .routes_decisions import router as decisions_router
from .routes_objects import router as objects_router
from .routes_phase2 import router as phase2_router
from .routes_procedures import router as procedures_router


def _default_kb_paths() -> tuple[Path, Path]:
    repo_root = Path(__file__).resolve().parents[2]
    kb_root = Path(os.getenv("AGENT_FOUNDATION_KB_ROOT", repo_root / "kb"))
    db_path = Path(os.getenv("AGENT_FOUNDATION_KB_DB", kb_root / "manifest.sqlite3"))
    return kb_root, db_path


def _default_tasks_root() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    return Path(os.getenv("AGENT_FOUNDATION_TASKS_ROOT", repo_root / "tasks"))


def _default_observability_root() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    return Path(os.getenv("AGENT_FOUNDATION_OBSERVABILITY_ROOT", repo_root / "observability"))


def create_app(
    store: Optional[ThinKBStore] = None,
    phase2_store: Optional[Phase2Store] = None,
    observability: Optional[Observability] = None,
) -> FastAPI:
    app = FastAPI(title="agent-foundation Thin KB API", version="0.1.0")
    if store is None:
        kb_root, db_path = _default_kb_paths()
        store = ThinKBStore(kb_root=kb_root, db_path=db_path)
    if phase2_store is None:
        phase2_store = Phase2Store(
            kb_root=store.kb_root,
            db_path=store.db_path,
            tasks_root=_default_tasks_root(),
            canonical_store=store,
        )
    install_observability(app, observability or Observability(_default_observability_root() / "thin_kb_api"))
    app.state.kb_store = store
    app.state.phase2_store = phase2_store
    app.include_router(claims_router)
    app.include_router(procedures_router)
    app.include_router(cases_router)
    app.include_router(decisions_router)
    app.include_router(objects_router)
    app.include_router(phase2_router)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
