# ADR-007: Promote Dagster for Wave 3 / Wave 4 orchestration

## Status

Accepted

## Context

Phase 2 introduced richer ingestion and retrieval, but the repo still lacked a reproducible way to:

- run frozen corpora
- compare historical runs
- attach asset checks and retries
- schedule replay smoke runs

`design-pack-v6` treats that orchestration layer as part of the next tranche.

## Decision

Promote `dagster==1.12.18` from deferred dependency to an active Phase 3 / Phase 4 dependency.

Use Dagster for:

- frozen corpus materialization
- replay and eval execution
- asset checks
- local nightly smoke scheduling

Do not use Dagster to replace existing API or storage boundaries.

## Consequences

- orchestration is now testable and repeatable
- replay/eval/shadow reporting share one execution graph
- public HTTP routes remain unchanged
- richer graph workflows are still deferred until evaluation data is stable
