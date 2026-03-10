# REVIEW_V8

## Review scope

This review assumes:
- Phase 2 implementation is complete
- the repository has already absorbed the v7 structural changes
- current Python tests pass
- the next goal is to make the system reliable, inspectable, replayable, and maintainable by AI-led workflows

This is an architecture- and repository-level review, not a line-by-line code audit.

---

## Executive summary

The project is now beyond "can it work" and has entered the stage where the biggest risks are:

1. **contract drift**
2. **event/audit weakness**
3. **evaluation being weaker than implementation velocity**
4. **runtime state, corpora, and generated outputs not having a hard enough home**
5. **agent-facing rules existing in docs but not yet enforced by repository shape and CI**
6. **too much maintenance logic remaining implicit instead of becoming first-class subsystems**

In other words: the current system is likely good enough to use, but not yet good enough to trust as a self-evolving AI-maintained project.

---

## What is still missing or underweighted

### A. Stronger contract system

The project needs a clearer distinction between:
- normative contracts
- generated contracts
- runtime payloads
- test fixtures

If this separation is weak, agents will modify the wrong layer.

### B. Event-sourcing lite

You do not need full event sourcing, but you do need append-only ledgers for:
- task state transitions
- artifact writes
- KB promotions/deprecations
- replay/eval runs
- release operations

Without this, replayability and postmortem quality stay mediocre.

### C. Eval as a product feature

Replay/eval should stop being test-adjacent and become a first-class subsystem.
The project should eventually be able to answer:
- Which change reduced retrieval quality?
- Which change increased human interventions?
- Which change worsened writeback promotion quality?
- Which change broke invariants in the task workflow?

### D. Operations model for AI maintenance

The repo should make it obvious how an AI maintenance agent is allowed to work:
- where it may write
- what it may regenerate
- what requires review
- how to run replay/eval before proposing a change
- how to produce a bounded migration

### E. Runtime boundary hardening

The code root and state root split is necessary, but not sufficient.
You also want:
- loopback-only services by default
- explicit read vs write paths
- per-service secret or shared token
- backups and restore drills
- migration commands and rollback commands

---

## Main architectural recommendation

The next wave should not be feature-first.
It should make four things first-class:

1. **contracts**
2. **events**
3. **eval/replay**
4. **operations**

Only after those are strong enough should you invest heavily in graph memory, graph retrieval, or more autonomous maintenance loops.
