# PLAN_V8

## Objective

Make the project operationally trustworthy and self-improvable.

The next wave is organized into four tracks:

1. **operational hardening**
2. **event and replay infrastructure**
3. **evaluation and CI gating**
4. **AI-maintenance ergonomics**

---

## Track 1 — Operational hardening

### Goals
- harden service boundaries
- separate read and write surfaces
- implement backup/restore drills
- make startup/config validation strict

### Deliverables
- service token/shared secret wiring
- loopback-only defaults
- backup + restore commands
- environment profile validation
- health and readiness endpoints

---

## Track 2 — Event and replay infrastructure

### Goals
- add append-only ledgers for all critical mutations
- support replay from stable manifests
- make artifact and KB changes reconstructable

### Deliverables
- task event schema
- KB event schema
- replay run event schema
- event writer integration
- replay manifest format
- replay runner CLI

---

## Track 3 — Evaluation and CI gating

### Goals
- make eval a release gate
- detect retrieval regressions
- detect workflow regressions
- detect contract drift automatically

### Deliverables
- retrieval gold set and metrics
- workflow eval dataset and metrics
- replay regression thresholds
- CI jobs for contracts, replay, eval

---

## Track 4 — AI-maintenance ergonomics

### Goals
- let Codex/review/maintenance agents work safely with less human context
- encode repository rules into scripts and checks, not only docs

### Deliverables
- agent task runner scripts
- one-command local validation
- maintenance checklists
- migration command templates
- release checklist generator

---

## Recommended execution order

### Wave 1
- service boundary hardening
- event ledgers
- replay manifests and runner

### Wave 2
- retrieval/workflow evaluation assets
- CI gating
- contract generation and drift checks

### Wave 3
- AI-maintenance workflow scripts
- weekly/nightly autonomous maintenance loops
- recovery drills and incident exercises

---

## Definition of done for v8 wave

This wave is done when:
- critical changes emit append-only events
- replay corpus exists and can run automatically
- retrieval and workflow eval exist and have thresholds
- services are boundary-hardened
- repo rules are enforceable by scripts/CI
- another agent can continue maintenance with only `AGENT_SYSTEM_README_V2.md` and the repo itself
