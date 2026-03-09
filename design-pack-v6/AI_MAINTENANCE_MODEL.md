# AI_MAINTENANCE_MODEL

The long-term goal is an AI-designed, AI-developed, AI-maintained, AI-evolving project.
That requires maintenance roles, not just implementation roles.

---

## Maintenance roles

### Maintainer Lead
Owns:
- prioritization
- change sequencing
- release gating
- escalation

### QA Steward
Owns:
- orthogonal test matrix
- test debt reduction
- flaky test triage
- coverage of invariants

### Eval Steward
Owns:
- gold datasets
- replay corpus
- retrieval metrics
- workflow quality metrics

### Knowledge Steward
Owns:
- candidate/trusted/deprecated lifecycle
- stale object cleanup
- writeback promotion reviews
- knowledge drift detection

### Release Steward
Owns:
- changelog
- release notes
- migration notes
- rollback instructions

### Infra Steward
Owns:
- backup/restore drills
- environment stability
- dependency review
- CI reliability

---

## Recurring loops

### Nightly
- API contract checks
- replay smoke corpus
- state machine invariant tests
- stale index detection

### Weekly
- retrieval evaluation
- writeback promotion review
- flaky test review
- dependency review
- backup restore drill summary

### Per release
- changelog generation
- migration check
- rollback checklist
- release readiness score

---

## Promotion logic

A capability moves from experimental to default only if:
- tests are present
- replay corpus passes
- metrics do not regress
- rollback path exists

---

## Human role

Human remains responsible for:
- final trust decisions
- architecture changes with broad impact
- security-sensitive changes
- deployment approvals

AI handles:
- design drafts
- implementation
- test generation
- regression triage
- maintenance loops
- documentation updates
