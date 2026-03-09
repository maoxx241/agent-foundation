# ROADMAP_PHASE2_5_TO_PHASE4

## Phase 2.5 — Stabilize
Purpose:
- freeze contracts
- harden workflow
- add observability
- expand tests

Exit criteria:
- 120+ tests
- state machine invariants green
- replay smoke corpus green
- backup/restore drill passes

## Phase 3 — Shadow mode
Purpose:
- run real tasks safely
- collect intervention data
- measure retrieval and workflow quality

Exit criteria:
- 5–10 real tasks completed
- intervention categories understood
- no critical boundary failures

## Phase 3.5 — Evaluation-driven tuning
Purpose:
- tune retrieval and writeback with evidence
- improve abstain behavior
- reduce wrong-version retrievals

Exit criteria:
- stable metric dashboard/report
- defined release gates for retrieval quality

## Phase 4 — AI-maintained engineering system
Purpose:
- hand recurring maintenance to specialized agents
- make onboarding of new agents fast and safe
- ensure repo remains self-describing

Exit criteria:
- maintenance roles documented
- weekly loops automated
- another agent can operate with README + ADRs alone
