from __future__ import annotations

from pathlib import Path

from packages.core.eval import load_eval_thresholds, load_gold_cases, load_replay_cases, load_shadow_manifest


def test_frozen_eval_corpora_load_from_repo():
    gold = load_gold_cases()
    replay = load_replay_cases()
    manifest = load_shadow_manifest(Path("evals/corpora/shadow/pilot_manifest.json"))
    thresholds = load_eval_thresholds(profile="full")

    assert len(gold) >= 10
    assert any(case.allow_abstain for case in gold)
    assert len(replay) >= 11
    assert any(case.kind == "workflow" for case in replay)
    assert len(manifest.cases) >= 2
    assert thresholds.min_replay_cases >= 11
