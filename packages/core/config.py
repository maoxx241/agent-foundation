from __future__ import annotations

import os
import sys
from pathlib import Path


def repo_root() -> Path:
    return _resolve(os.getenv("AGENT_FOUNDATION_REPO_ROOT"), Path(__file__).resolve().parents[2])


def state_root() -> Path:
    return _resolve(os.getenv("AGENT_FOUNDATION_STATE_ROOT"), _default_state_root())


def workspace_root() -> Path:
    return _resolve(os.getenv("AGENT_FOUNDATION_WORKSPACE_ROOT"), _default_workspace_root())


def tasks_root() -> Path:
    return _resolve(os.getenv("AGENT_FOUNDATION_TASKS_ROOT"), state_root() / "tasks")


def tasks_active_root() -> Path:
    return tasks_root() / "active"


def tasks_archived_root() -> Path:
    return tasks_root() / "archived"


def kb_root() -> Path:
    return _resolve(os.getenv("AGENT_FOUNDATION_KB_ROOT"), state_root() / "kb")


def kb_canonical_root() -> Path:
    return kb_root() / "canonical"


def kb_candidates_root() -> Path:
    return kb_root() / "candidates"


def kb_deprecated_root() -> Path:
    return kb_root() / "deprecated"


def kb_db_path() -> Path:
    return _resolve(os.getenv("AGENT_FOUNDATION_KB_DB"), sqlite_indexes_root() / "manifest.sqlite3")


def observability_root() -> Path:
    return _resolve(os.getenv("AGENT_FOUNDATION_OBSERVABILITY_ROOT"), state_root() / "observability")


def evals_root() -> Path:
    return _resolve(os.getenv("AGENT_FOUNDATION_EVALS_ROOT") or os.getenv("AGENT_FOUNDATION_EVAL_ROOT"), repo_root() / "evals")


def generated_root() -> Path:
    return _resolve(os.getenv("AGENT_FOUNDATION_GENERATED_ROOT"), repo_root() / "generated")


def contracts_root() -> Path:
    return repo_root() / "contracts"


def reports_root() -> Path:
    return _resolve(os.getenv("AGENT_FOUNDATION_REPORTS_ROOT"), generated_root() / "reports")


def shadow_runs_root() -> Path:
    return _resolve(os.getenv("AGENT_FOUNDATION_SHADOW_RUNS_ROOT"), replay_captured_runs_root())


def replay_root() -> Path:
    return state_root() / "replay"


def replay_captured_runs_root() -> Path:
    return replay_root() / "captured_runs"


def backups_root() -> Path:
    return state_root() / "backups"


def indexes_root() -> Path:
    return state_root() / "indexes"


def sqlite_indexes_root() -> Path:
    return indexes_root() / "sqlite"


def lancedb_indexes_root() -> Path:
    return indexes_root() / "lancedb"


def ledgers_root() -> Path:
    return state_root() / "ledgers"


def task_ledgers_root() -> Path:
    return ledgers_root() / "task_events"


def kb_ledgers_root() -> Path:
    return ledgers_root() / "kb_events"


def audit_ledgers_root() -> Path:
    return ledgers_root() / "audits"


def replay_run_ledgers_root() -> Path:
    return ledgers_root() / "replay_runs"


def release_ledgers_root() -> Path:
    return ledgers_root() / "releases"


def worktrees_root() -> Path:
    return workspace_root() / "worktrees"


def sandboxes_root() -> Path:
    return workspace_root() / "sandboxes"


def agent_tmp_root() -> Path:
    return workspace_root() / "agent_tmp"


def agent_token() -> str:
    return os.getenv("AGENT_FOUNDATION_AGENT_TOKEN", "agent-token")


def operator_token() -> str:
    return os.getenv("AGENT_FOUNDATION_OPERATOR_TOKEN", "operator-token")


def ensure_state_layout() -> dict[str, Path]:
    layout = {
        "state_root": state_root(),
        "tasks_root": tasks_root(),
        "tasks_active_root": tasks_active_root(),
        "tasks_archived_root": tasks_archived_root(),
        "kb_root": kb_root(),
        "kb_canonical_root": kb_canonical_root(),
        "kb_candidates_root": kb_candidates_root(),
        "kb_deprecated_root": kb_deprecated_root(),
        "indexes_root": indexes_root(),
        "sqlite_indexes_root": sqlite_indexes_root(),
        "lancedb_indexes_root": lancedb_indexes_root(),
        "ledgers_root": ledgers_root(),
        "task_ledgers_root": task_ledgers_root(),
        "kb_ledgers_root": kb_ledgers_root(),
        "audit_ledgers_root": audit_ledgers_root(),
        "replay_run_ledgers_root": replay_run_ledgers_root(),
        "release_ledgers_root": release_ledgers_root(),
        "observability_root": observability_root(),
        "replay_root": replay_root(),
        "replay_captured_runs_root": replay_captured_runs_root(),
        "shadow_runs_root": shadow_runs_root(),
        "backups_root": backups_root(),
    }
    for path in layout.values():
        path.mkdir(parents=True, exist_ok=True)
    return layout


def ensure_workspace_layout() -> dict[str, Path]:
    layout = {
        "workspace_root": workspace_root(),
        "worktrees_root": worktrees_root(),
        "sandboxes_root": sandboxes_root(),
        "agent_tmp_root": agent_tmp_root(),
    }
    for path in layout.values():
        path.mkdir(parents=True, exist_ok=True)
    return layout


def ensure_runtime_layout() -> dict[str, dict[str, Path]]:
    return {
        "state": ensure_state_layout(),
        "workspace": ensure_workspace_layout(),
    }


def validate_runtime_roots() -> None:
    repo = repo_root()
    configured = {
        "AGENT_FOUNDATION_STATE_ROOT": state_root(),
        "AGENT_FOUNDATION_TASKS_ROOT": tasks_root(),
        "AGENT_FOUNDATION_KB_ROOT": kb_root(),
        "AGENT_FOUNDATION_OBSERVABILITY_ROOT": observability_root(),
        "AGENT_FOUNDATION_WORKSPACE_ROOT": workspace_root(),
    }
    derived = {
        "indexes_root": indexes_root(),
        "ledgers_root": ledgers_root(),
        "replay_root": replay_root(),
        "backups_root": backups_root(),
        "shadow_runs_root": shadow_runs_root(),
    }
    repo_local = [name for name, path in {**configured, **derived}.items() if path.is_relative_to(repo)]
    if repo_local:
        joined = ", ".join(sorted(repo_local))
        raise RuntimeError(f"Runtime roots must live outside the repo root; repo-local paths detected for: {joined}")


def legacy_repo_runtime_paths() -> list[Path]:
    repo = repo_root()
    return [
        repo / "tasks",
        repo / "kb",
        repo / "observability",
        repo / "reports",
        repo / "shadow_runs",
    ]


def _resolve(value: str | None, default: Path) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    return default.expanduser().resolve()


def _default_state_root() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "agent-foundation"
    if os.name == "nt":
        local_appdata = os.getenv("LOCALAPPDATA")
        if local_appdata:
            return Path(local_appdata) / "agent-foundation"
        return Path.home() / "AppData" / "Local" / "agent-foundation"
    xdg_state_home = os.getenv("XDG_STATE_HOME")
    if xdg_state_home:
        return Path(xdg_state_home) / "agent-foundation"
    return Path.home() / ".local" / "state" / "agent-foundation"


def _default_workspace_root() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "agent-foundation-work"
    if os.name == "nt":
        local_appdata = os.getenv("LOCALAPPDATA")
        if local_appdata:
            return Path(local_appdata) / "agent-foundation-work"
        return Path.home() / "AppData" / "Local" / "agent-foundation-work"
    xdg_state_home = os.getenv("XDG_STATE_HOME")
    if xdg_state_home:
        return Path(xdg_state_home) / "agent-foundation-work"
    return Path.home() / ".local" / "state" / "agent-foundation-work"
