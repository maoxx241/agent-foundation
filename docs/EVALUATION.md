# Evaluation

## Frozen corpora

- Retrieval gold sets: `evals/datasets/gold/*.jsonl`
- Replay smoke corpus: `evals/corpora/replay/*.jsonl`
- Shadow manifests: `evals/corpora/shadow/*.json`

## Outputs

- Raw and aggregate eval outputs: `generated/reports/eval/<run_id>/`
- Main artifacts:
  - `run.json`
  - `retrieval-results.json`
  - `replay-results.json`
  - `report.md`
  - `comparison.json` when a baseline is provided

## Commands

```bash
.venv/bin/python scripts/generate_eval_report.py
.venv/bin/python scripts/materialize_eval_assets.py --run-id nightly-smoke
.venv/bin/python scripts/compare_eval_runs.py baseline-run candidate-run
```
