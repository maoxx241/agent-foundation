from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from libs.schemas import GoldQueryCase, ReplayCase, ShadowPilotManifest

T = TypeVar("T", bound=BaseModel)


def default_eval_root() -> Path:
    return Path(__file__).resolve().parents[2] / "eval"


def load_gold_cases(root: Path | None = None) -> list[GoldQueryCase]:
    root = root or default_eval_root()
    cases: list[GoldQueryCase] = []
    for path in sorted((root / "gold").glob("*.jsonl")):
        cases.extend(_load_jsonl(path, GoldQueryCase))
    return cases


def load_replay_cases(root: Path | None = None) -> list[ReplayCase]:
    root = root or default_eval_root()
    cases: list[ReplayCase] = []
    for path in sorted((root / "replay").glob("*.jsonl")):
        cases.extend(_load_jsonl(path, ReplayCase))
    return cases


def load_shadow_manifest(path: Path) -> ShadowPilotManifest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ShadowPilotManifest.model_validate(payload)


def _load_jsonl(path: Path, model: type[T]) -> list[T]:
    records: list[T] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records.append(model.model_validate_json(line))
    return records
