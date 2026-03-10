from __future__ import annotations

import os
import sys
from pathlib import Path


def repo_root() -> Path:
    return _resolve(os.getenv("AGENT_FOUNDATION_REPO_ROOT"), Path(__file__).resolve().parents[2])


def state_root() -> Path:
    return _resolve(os.getenv("AGENT_FOUNDATION_STATE_ROOT"), _default_state_root())


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
    return _resolve(os.getenv("AGENT_FOUNDATION_SHADOW_RUNS_ROOT"), state_root() / "replay" / "captured_runs")


def replay_root() -> Path:
    return state_root() / "replay"


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
        "observability_root": observability_root(),
        "replay_root": replay_root(),
        "shadow_runs_root": shadow_runs_root(),
        "backups_root": backups_root(),
    }
    for path in layout.values():
        path.mkdir(parents=True, exist_ok=True)
    return layout


def validate_runtime_roots() -> None:
    repo = repo_root()
    configured = [tasks_root(), kb_root(), observability_root()]
    if any(path.is_relative_to(repo) for path in configured):
        explicit = {
            "AGENT_FOUNDATION_TASKS_ROOT": os.getenv("AGENT_FOUNDATION_TASKS_ROOT"),
            "AGENT_FOUNDATION_KB_ROOT": os.getenv("AGENT_FOUNDATION_KB_ROOT"),
            "AGENT_FOUNDATION_OBSERVABILITY_ROOT": os.getenv("AGENT_FOUNDATION_OBSERVABILITY_ROOT"),
        }
        if any(value for value in explicit.values()):
            raise RuntimeError("Repo-local runtime overrides are not allowed once STATE_ROOT mode is enabled")


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
