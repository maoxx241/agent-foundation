# CODEX_NEXT_WAVE

This file tells Codex what to do after Phase 2.

## Goal
Turn the current implementation into a stable, test-rich, shadow-mode-capable system.

## Order of work

### Wave 1: Stabilization
1. Freeze public API contracts
2. Harden state machine transitions
3. Add backup/restore scripts and docs
4. Add structured logging and metrics hooks

### Wave 2: Test expansion
5. Implement all A-* and W-* tests from `TEST_MATRIX_PHASE2_5.md`
6. Implement K-* and M-* tests
7. Implement D-* and T-* tests
8. Implement L-* and G-* tests
9. Implement R-* and S-* tests

### Wave 3: Evaluation system
10. Build gold query datasets
11. Build replay corpus loader
12. Add metric computation scripts
13. Add report generation

### Wave 4: Shadow mode support
14. Add intervention logging
15. Add run summary generation
16. Add regression comparison report

## Hard rules
- Tests are part of the deliverable.
- Do not introduce new third-party dependencies without updating `DEPENDENCIES.md` and ADR.
- Do not weaken plane boundaries.
- Do not hide failures; expose explicit errors.

## Minimum completion bar
- 120+ tests
- replay corpus support
- retrieval metric report
- shadow mode checklist
