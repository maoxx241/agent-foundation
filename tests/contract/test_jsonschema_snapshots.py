from __future__ import annotations

import json
from pathlib import Path

from packages.core.contracts import build_jsonschema_contracts


def _snapshot_root() -> Path:
    return Path(__file__).resolve().parents[2] / "contracts" / "jsonschema"


def test_jsonschema_snapshots_match_runtime_models():
    generated = build_jsonschema_contracts()
    for name, payload in generated.items():
        expected = json.loads((_snapshot_root() / name).read_text(encoding="utf-8"))
        assert payload == expected
