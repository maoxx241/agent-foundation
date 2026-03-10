# TEST_MATRIX_PHASE2_5

This matrix assumes Phase 2 is implemented.
The goal is to convert the project from “working implementation” to “reliable engineering system”.

Each group has:
- target scope
- minimum case count
- what must be automated

---

## A. Artifact API

| ID | Area | Scenario | Expected |
|---|---|---|---|
| A-01 | task create | create valid task | task created, state=NEW |
| A-02 | task create | duplicate task_id | explicit conflict/error |
| A-03 | task get | missing task | 404 |
| A-04 | artifact put | valid stage/file write | persisted + retrievable |
| A-05 | artifact put | invalid stage | rejected |
| A-06 | artifact put | malformed schema payload | rejected |
| A-07 | artifact list | task with multiple stages | correct manifest |
| A-08 | state update | legal transition | accepted |
| A-09 | state update | illegal transition | rejected |
| A-10 | finalize writeback | before VALIDATED | rejected |
| A-11 | finalize writeback | after VALIDATED | accepted |
| A-12 | idempotency | same PUT twice | no corruption |
| A-13 | concurrent write | same file concurrent updates | deterministic winner/lock |
| A-14 | bundle export | full task bundle | complete and consistent |

Minimum automated count: **20**

---

## W. Workflow / state machine

| ID | Area | Scenario | Expected |
|---|---|---|---|
| W-01 | happy path | full lifecycle | reaches WRITTEN_BACK |
| W-02 | review reject | design review rejects | returns to design stage |
| W-03 | self-test fail | impl incomplete | remains IMPLEMENTED |
| W-04 | impl review reject | patch not approved | returns IMPLEMENTED |
| W-05 | validation bug | validation fails due to code | returns IMPLEMENTED |
| W-06 | validation spec | validation fails due to spec | returns DESIGN_APPROVED/TESTSPEC_FROZEN |
| W-07 | repeated finalize | duplicate finalize | idempotent |
| W-08 | missing artifact | skip required artifact | blocked |
| W-09 | restart recovery | restart mid-task | state recoverable |
| W-10 | partial rollback | restore previous artifact | state remains consistent |

Minimum automated count: **20**

Recommended implementation:
- Hypothesis RuleBasedStateMachine
- explicit invariants for legal transitions and required artifacts

---

## M. Memory integration

| ID | Area | Scenario | Expected |
|---|---|---|---|
| M-01 | store | store user memory | retrievable |
| M-02 | search | semantic recall works | relevant results |
| M-03 | list | scoped listing | correct scope |
| M-04 | get | direct fetch | exact object |
| M-05 | forget | deletion/removal | no longer retrievable |
| M-06 | isolation | user/project/session boundaries | no cross-leak |
| M-07 | auto-capture | memory extracted from interaction | visible later |
| M-08 | auto-recall | recall injected when relevant | improves context |
| M-09 | duplicate memory | same fact repeated | deduplicated or stable |
| M-10 | conflict | conflicting memory entries | handled explicitly |

Minimum automated count: **12**

---

## K. Thin KB canonical + API

| ID | Area | Scenario | Expected |
|---|---|---|---|
| K-01 | claim create | valid claim | persisted |
| K-02 | procedure create | valid procedure | persisted |
| K-03 | case create | valid case | persisted |
| K-04 | decision create | valid decision | persisted |
| K-05 | status lifecycle | candidate->trusted | valid only if rule passes |
| K-06 | deprecated lifecycle | trusted->deprecated | visible in status |
| K-07 | get object | existing object | exact return |
| K-08 | search exact | term match | result found |
| K-09 | search tag | domain/scope filter | correct subset |
| K-10 | related | related objects returned | linked objects only |
| K-11 | bad schema | invalid object shape | rejected |
| K-12 | manifest consistency | file + manifest mismatch | detected |

Minimum automated count: **20**

---

## D. Docling parsing

| ID | Area | Scenario | Expected |
|---|---|---|---|
| D-01 | pdf parse | normal PDF | parse succeeds |
| D-02 | docx parse | normal DOCX | parse succeeds |
| D-03 | html parse | normal HTML | parse succeeds |
| D-04 | determinism | same file twice | stable extract structure |
| D-05 | table extraction | table-heavy doc | table preserved |
| D-06 | code block extraction | code-heavy doc | code preserved |
| D-07 | malformed file | damaged input | graceful failure |
| D-08 | metadata extraction | title/sections/pages | metadata usable |

Minimum automated count: **12**

---

## T. Tree-sitter extraction

| ID | Area | Scenario | Expected |
|---|---|---|---|
| T-01 | parse python file | valid file | tree produced |
| T-02 | symbol extraction | function/class/module | correct entities |
| T-03 | config extraction | constants/env/config fields | correct extracts |
| T-04 | syntax error file | broken code | graceful partial parse |
| T-05 | incremental update | small file edit | delta extraction stable |
| T-06 | test extraction | test cases identified | expected test nodes |
| T-07 | alias handling | imports/renames | stable entity naming |
| T-08 | edge syntax | decorators/type hints/match | no silent loss |

Minimum automated count: **12**

---

## L. LanceDB retrieval

| ID | Area | Scenario | Expected |
|---|---|---|---|
| L-01 | FTS exact | exact term query | correct hit |
| L-02 | vector semantic | paraphrase query | relevant hit |
| L-03 | hybrid search | mixed exact+semantic | strong combined ranking |
| L-04 | rerank | top-k reorder | better top results |
| L-05 | version filter | environment/version query | wrong versions suppressed |
| L-06 | empty query | no result / safe behavior | abstain |
| L-07 | stale object | deprecated filtered | not promoted unless requested |
| L-08 | duplicate docs | same content multiple times | dedupe stable |
| L-09 | wrong-domain query | domain mismatch | low/no retrieval |
| L-10 | benchmarked query | known gold query | hit@k threshold met |

Minimum automated count: **16**

---

## G. Dagster pipeline

| ID | Area | Scenario | Expected |
|---|---|---|---|
| G-01 | full materialization | raw -> objects -> views -> index | succeeds |
| G-02 | partial recompute | upstream changed subset | only affected assets update |
| G-03 | failed asset | parser failure | downstream blocked appropriately |
| G-04 | asset check | schema completeness | check fails on bad object |
| G-05 | publish check | candidate/trusted rules | enforced |
| G-06 | retry | transient failure | recoverable |
| G-07 | lineage | asset lineage present | traceable |
| G-08 | schedule | periodic run | stable + repeatable |

Minimum automated count: **12**

---

## R. Recovery and backup

| ID | Area | Scenario | Expected |
|---|---|---|---|
| R-01 | artifact restore | restore tasks/ | task recoverable |
| R-02 | kb restore | restore canonical objects | search works after rebuild |
| R-03 | index rebuild | rebuild from canonical | deterministic results |
| R-04 | manifest corruption | broken manifest | corruption detected |
| R-05 | partial backup | missing subset | explicit failure |
| R-06 | memory reconnect | memory service restart | recall/store recovers |

Minimum automated count: **8**

---

## S. Security / boundary tests

| ID | Area | Scenario | Expected |
|---|---|---|---|
| S-01 | task isolation | task A cannot read task B private artifacts |
| S-02 | memory scope | user/project/session boundaries enforced |
| S-03 | API validation | unknown fields rejected or ignored per policy |
| S-04 | path traversal | invalid path inputs rejected |
| S-05 | adapter boundary | OpenClaw tools cannot bypass API constraints |
| S-06 | malformed payload flood | service remains stable |

Minimum automated count: **8**

---

## Minimum suite targets

- A + W: mandatory before any further rollout
- K + M: mandatory before AI-maintained loops
- D + T + L + G: mandatory before Phase 2 is considered stable
- R + S: mandatory before shadow mode

Recommended total automated count:

- Minimum acceptable: **120**
- Strong baseline: **150+**
- Long-term target: **200+**
