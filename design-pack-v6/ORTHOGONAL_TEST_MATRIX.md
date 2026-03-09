# ORTHOGONAL_TEST_MATRIX

## Goal

Expand Phase 1 tests without exploding the number of cases.
Use orthogonal / pairwise-style design for the highest-risk dimensions.

## Why this is needed

Naive cross-product testing becomes too large very quickly.
For a 4-factor / 3-level matrix:

N_full = 3^4 = 81

Using an L9 orthogonal array:

N_oa = 9

Reduction:

reduction = 1 - 9 / 81 = 0.8889 = 88.89%

Verification:
- 3^4 = 81
- 9 / 81 = 0.1111
- 1 - 0.1111 = 0.8889

Use orthogonal matrices for high-value functional combinations.
Use property-based testing and contract fuzzing to cover the long tail.

## Test stack

- pytest: baseline runner, fixtures, parametrization
- hypothesis: property-based tests for schemas / invariants
- schemathesis: OpenAPI-driven API fuzzing and stateful sequences
- httpx: API client tests
- pytest-asyncio: async API tests when needed
- pytest-xdist: optional parallel test execution

## Layer A: Artifact API matrix (L9)

Factors:
- A1 Stage:
  - 1 = NEW/EVIDENCE stage
  - 2 = DESIGN/TEST stage
  - 3 = VALIDATION/WRITEBACK stage
- A2 Payload shape:
  - 1 = minimal valid
  - 2 = full valid
  - 3 = invalid / missing required field
- A3 State transition:
  - 1 = legal
  - 2 = illegal forward
  - 3 = illegal backward
- A4 Storage precondition:
  - 1 = clean task dir
  - 2 = existing artifact / idempotent overwrite
  - 3 = partial or missing dependent file

| Case | Stage | Payload | Transition | Storage | Expected |
|---|---:|---:|---:|---:|---|
| A-01 | 1 | 1 | 1 | 1 | success |
| A-02 | 1 | 2 | 2 | 2 | reject transition |
| A-03 | 1 | 3 | 3 | 3 | schema error |
| A-04 | 2 | 1 | 2 | 3 | reject transition |
| A-05 | 2 | 2 | 3 | 1 | reject transition |
| A-06 | 2 | 3 | 1 | 2 | schema error |
| A-07 | 3 | 1 | 3 | 2 | reject transition |
| A-08 | 3 | 2 | 1 | 3 | fail with dependency error |
| A-09 | 3 | 3 | 2 | 1 | schema error |

## Layer B: Thin KB search matrix (L9)

Factors:
- B1 Object type:
  - 1 = Claim
  - 2 = Procedure
  - 3 = Case/Decision
- B2 Status filter:
  - 1 = trusted
  - 2 = candidate
  - 3 = deprecated
- B3 Query mode:
  - 1 = exact id/title
  - 2 = tag filter
  - 3 = full-text contains
- B4 Version condition:
  - 1 = no version supplied
  - 2 = version matches object
  - 3 = version mismatch

| Case | Type | Status | Query | Version | Expected |
|---|---:|---:|---:|---:|---|
| K-01 | 1 | 1 | 1 | 1 | exact object returned |
| K-02 | 1 | 2 | 2 | 2 | candidate object returned |
| K-03 | 1 | 3 | 3 | 3 | empty or deprecated-only handling |
| K-04 | 2 | 1 | 2 | 3 | filtered out by version |
| K-05 | 2 | 2 | 3 | 1 | matching candidate procedures |
| K-06 | 2 | 3 | 1 | 2 | deprecated procedure by exact lookup |
| K-07 | 3 | 1 | 3 | 2 | matching case/decision by text |
| K-08 | 3 | 2 | 1 | 3 | exact object found but version flagged |
| K-09 | 3 | 3 | 2 | 1 | deprecated filtered search |

## Layer C: Memory integration matrix (L9)

Factors:
- C1 Scope:
  - 1 = user
  - 2 = project
  - 3 = task/session
- C2 Recall mode:
  - 1 = no hit
  - 2 = single hit
  - 3 = multiple hits
- C3 Capture mode:
  - 1 = auto capture success
  - 2 = manual store only
  - 3 = capture failure / degraded
- C4 Backend condition:
  - 1 = healthy
  - 2 = slow / retry
  - 3 = unavailable

| Case | Scope | Recall | Capture | Backend | Expected |
|---|---:|---:|---:|---:|---|
| M-01 | 1 | 1 | 1 | 1 | graceful no-hit + store success |
| M-02 | 1 | 2 | 2 | 2 | recall success + manual store |
| M-03 | 1 | 3 | 3 | 3 | degrade gracefully |
| M-04 | 2 | 1 | 2 | 3 | no-hit + degraded store |
| M-05 | 2 | 2 | 3 | 1 | hit + capture error surfaced |
| M-06 | 2 | 3 | 1 | 2 | multi-hit + capture success |
| M-07 | 3 | 1 | 3 | 2 | no-hit + capture error |
| M-08 | 3 | 2 | 1 | 3 | hit + backend unavailable |
| M-09 | 3 | 3 | 2 | 1 | multi-hit + manual store |

## Layer D: Workflow matrix (L8, binary)

Factors:
- D1 Design review: approve / reject
- D2 Test plan quality: valid / invalid
- D3 Impl review: approve / reject
- D4 Validation: pass / fail
- D5 Writeback eligibility: yes / no

| Case | D1 | D2 | D3 | D4 | D5 | Expected |
|---|---:|---:|---:|---:|---:|---|
| W-01 | 0 | 0 | 0 | 0 | 0 | blocked early |
| W-02 | 0 | 0 | 1 | 1 | 1 | impossible path must not occur |
| W-03 | 0 | 1 | 0 | 1 | 1 | impossible path must not occur |
| W-04 | 0 | 1 | 1 | 0 | 0 | blocked before validation |
| W-05 | 1 | 0 | 0 | 1 | 0 | blocked at test-plan gate |
| W-06 | 1 | 0 | 1 | 0 | 0 | blocked at test-plan gate |
| W-07 | 1 | 1 | 0 | 0 | 0 | returns to implementation |
| W-08 | 1 | 1 | 1 | 1 | 1 | happy path |

## Property-based supplement

Orthogonal matrices do not replace fuzzing.
Add Hypothesis tests for:
- schema round-trip and serialization invariants
- state machine invariants
- artifact path normalization and invalid filenames
- Thin KB search result typing invariants

## Contract fuzzing supplement

Run Schemathesis against:
- artifact_api.yaml
- thin_kb_api.yaml

Required assertions:
- response conforms to schema
- invalid payloads are rejected consistently
- no 500 on malformed but validly-shaped requests
- stateful task sequences do not violate workflow invariants

## Execution priority

Implement in this order:
1. A-01..A-09
2. W-08 and blocked-path checks
3. K-01..K-09
4. M-01..M-09
5. property-based tests
6. Schemathesis contract runs
