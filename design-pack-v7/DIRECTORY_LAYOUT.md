# DIRECTORY_LAYOUT

## Repository layout

```text
agent-foundation/
  apps/
    artifact_api/
      main.py
      routes_tasks.py
      routes_artifacts.py
      routes_writeback.py
    thin_kb_api/
      main.py
      routes_claims.py
      routes_procedures.py
      routes_cases.py
      routes_decisions.py

  libs/
    schemas/
      common.py
      artifacts.py
      thin_kb.py
    storage/
      artifact_store.py
      thin_kb_store.py
      state_machine.py
      fs_utils.py

  openclaw/
    plugin_adapter/
      package.json
      tsconfig.json
      src/
        index.ts
        client/
          api.ts
        tools/
          artifact.ts
          kb.ts

  tasks/
    <task_id>/
      00_task/
        task-brief.json
        state.json
      10_evidence/
        evidence-pack.json
        gaps.json
      20_design/
        design-main.md
        design-alt.md
        design-spec.md
        design-review.md
      30_test/
        test-spec.json
        acceptance.json
      40_dev/
        patch.diff
        changed-files.json
        selftest.json
        dev-notes.md
      50_review/
        impl-review.md
      60_validation/
        validation-report.json
        regression.json
        perf.json
      70_release/
        adr.md
        changelog.md
        incident-summary.md
      80_writeback/
        experience-packet.json
        attachments.json

  kb/
    canonical/
      claims/
      procedures/
      cases/
      decisions/

  tests/
    unit/
    e2e/
```

## Notes

- `tasks/` is the active workflow truth store.
- `kb/canonical/` is the thin canonical knowledge store.
- `openclaw/plugin_adapter/` should remain thin and stateless.
