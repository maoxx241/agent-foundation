# STATE_MACHINE

## States

```text
NEW
EVIDENCE_READY
DESIGN_APPROVED
TESTSPEC_FROZEN
IMPLEMENTED
IMPL_APPROVED
VALIDATED
RELEASED
WRITTEN_BACK
```

## Transition rules

### NEW -> EVIDENCE_READY
Required:
- task-brief.json
- evidence-pack.json

### EVIDENCE_READY -> DESIGN_APPROVED
Required:
- design-spec.md
- design-review.md with approved or approved_with_conditions resolved

### DESIGN_APPROVED -> TESTSPEC_FROZEN
Required:
- test-spec.json
- acceptance.json

### TESTSPEC_FROZEN -> IMPLEMENTED
Required:
- patch.diff
- changed-files.json
- selftest.json

### IMPLEMENTED -> IMPL_APPROVED
Required:
- impl-review.md with approved or approved_with_conditions resolved

### IMPL_APPROVED -> VALIDATED
Required:
- validation-report.json
- regression.json
- perf.json if relevant

### VALIDATED -> RELEASED
Required:
- adr.md
- changelog.md
- incident-summary.md if relevant

### RELEASED -> WRITTEN_BACK
Required:
- experience-packet.json
- writeback finalization success

## Rollback rules

- Design failure returns to EVIDENCE_READY or DESIGN_APPROVED, depending on what remains valid.
- Self-test failure remains in IMPLEMENTED.
- Impl review rejection returns to IMPLEMENTED.
- Validation bug returns to IMPLEMENTED.
- Validation spec failure returns to DESIGN_APPROVED or TESTSPEC_FROZEN.

## Invariants

1. No code implementation begins before test planning is frozen.
2. No writeback finalization occurs before validation succeeds or failure is fully characterized.
3. State transitions are validated server-side, not only in prompts.
