from __future__ import annotations

import pytest

from packages.core.config import validate_runtime_roots


def test_validate_runtime_roots_rejects_repo_local_state_and_workspace(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setenv("AGENT_FOUNDATION_REPO_ROOT", str(repo_root))
    monkeypatch.setenv("AGENT_FOUNDATION_STATE_ROOT", str(repo_root / "state"))
    monkeypatch.setenv("AGENT_FOUNDATION_WORKSPACE_ROOT", str(repo_root / "work"))

    with pytest.raises(RuntimeError, match="Runtime roots must live outside the repo root"):
        validate_runtime_roots()
