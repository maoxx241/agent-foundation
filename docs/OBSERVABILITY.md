# Observability

## Storage

Observability data is written locally under:

- `observability/artifact_api/events.jsonl`
- `observability/artifact_api/metrics.jsonl`
- `observability/thin_kb_api/events.jsonl`
- `observability/thin_kb_api/metrics.jsonl`

Override root with:

- `AGENT_FOUNDATION_OBSERVABILITY_ROOT`

## Trace IDs

- Every API request gets an `x-trace-id`
- If the caller sends one, it is preserved
- If the caller does not send one, the service generates one
- The OpenClaw adapter now forwards an `x-trace-id` automatically
- `x-run-id` is optional and groups multiple requests into one eval or shadow run

## Event coverage

Structured events currently include:

- task creation
- task state update / rejection
- writeback finalization / rejection
- document and code ingestion
- KB publish/refine
- human intervention records when logged during shadow mode
- request completion and request failure

## Metrics report

Generate a local report:

```bash
.venv/bin/python scripts/generate_metrics_report.py --observability-root observability/artifact_api
```

Current report fields include:

- request totals and error totals
- retrieval latency summary
- validation fail rate
- writeback promotion rate
- human intervention rate hook
