from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from packages.core.config import evals_root
from packages.core.schemas import EvalThresholds, GoldQueryCase, ReplayCase, ShadowPilotManifest

T = TypeVar("T", bound=BaseModel)


def default_eval_root() -> Path:
    return evals_root()


def load_gold_cases(root: Path | None = None) -> list[GoldQueryCase]:
    root = root or default_eval_root()
    cases: list[GoldQueryCase] = []
    for path in sorted((root / "datasets" / "gold").glob("*.jsonl")):
        cases.extend(_load_jsonl(path, GoldQueryCase))
    return cases


def load_replay_cases(root: Path | None = None) -> list[ReplayCase]:
    root = root or default_eval_root()
    cases: list[ReplayCase] = []
    for path in sorted((root / "corpora" / "replay").glob("*.jsonl")):
        cases.extend(_load_jsonl(path, ReplayCase))
    return cases


def load_shadow_manifest(path: Path) -> ShadowPilotManifest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ShadowPilotManifest.model_validate(payload)


def load_eval_thresholds(
    root: Path | None = None,
    *,
    path: Path | None = None,
    profile: str = "smoke",
) -> EvalThresholds:
    if path is not None:
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        root = root or default_eval_root()
        payload = json.loads((root / "manifests" / "thresholds.json").read_text(encoding="utf-8"))

    selected = payload.get("profiles", {}).get(profile, payload)
    selected = dict(selected)
    selected.setdefault("profile", profile)
    return EvalThresholds.model_validate(selected)


def _load_jsonl(path: Path, model: type[T]) -> list[T]:
    records: list[T] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records.append(model.model_validate_json(line))
    return records
