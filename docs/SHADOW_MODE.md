# Shadow Mode

## Storage

- Isolated workspaces: `shadow_runs/<run_id>/`
- Shadow reports: `reports/shadow/<run_id>/`

## Safety defaults

- `x-run-id` is used to correlate requests and logs
- `kb/writeback/refine` is forced to `persist=false` in the shadow pilot runner
- Promotion is a separate explicit follow-up step

## Outputs

- `run-summary.json`
- `shadow-checklist.md`
- `interventions.jsonl`

## Commands

```bash
.venv/bin/python scripts/run_shadow_pilot.py --run-id shadow-smoke
.venv/bin/python scripts/log_intervention.py shadow-smoke task-id 60_validation regression_escape high manual_fix --notes "human caught it"
.venv/bin/python scripts/generate_shadow_summary.py shadow-smoke
```
