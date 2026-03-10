# Review

- Prioritize state-boundary regressions, auth bypasses, contract drift, and ledger completeness.
- For public APIs, verify `v1` paths remain stable and changes are additive only.
- For KB mutations, check that only operator endpoints can publish trusted canonical objects.
- Reject changes that write runtime state back into repo-local `tasks/`, `kb/`, `observability/`, `reports/`, or `shadow_runs/`.
