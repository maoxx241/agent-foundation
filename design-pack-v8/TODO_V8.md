# TODO_V8

## P0 — Must do first

### P0-1 Contract unification
- [ ] ensure `contracts/` is the only normative contract root
- [ ] generate `generated/openapi/` and `generated/jsonschema/` from source
- [ ] add CI check that fails on contract drift

### P0-2 Service boundary hardening
- [ ] bind all local services to loopback by default
- [ ] add shared secret / service token between OpenClaw adapter and backend APIs
- [ ] split read and write credentials where practical
- [ ] add startup validation for required env vars and path roots

### P0-3 Event ledgers
- [ ] define `TaskEvent` schema
- [ ] define `KBEvent` schema
- [ ] define `ReplayRunEvent` schema
- [ ] write append-only ledger sinks under state root
- [ ] emit events for state transitions, artifact writes, KB promote/deprecate, replay/eval runs

Acceptance:
- every critical mutation is visible in an append-only ledger

---

## P1 — Replay and eval become first-class

### P1-1 Replay subsystem
- [ ] create `evals/corpora/replay/`
- [ ] define replay case manifest schema
- [ ] add replay runner CLI
- [ ] add replay report JSON schema
- [ ] freeze at least 10 real replay cases

### P1-2 Retrieval eval
- [ ] create gold datasets for fact/how-to/troubleshooting/design/validation
- [ ] implement metrics: hit@1/3/5, MRR, wrong-version rate, abstain precision
- [ ] set initial fail thresholds for CI/nightly runs

### P1-3 Workflow eval
- [ ] track design acceptance rate
- [ ] track impl rejection rate
- [ ] track validation fail rate
- [ ] track writeback promotion rate
- [ ] track human intervention rate

Acceptance:
- replay and eval can run from one command and produce machine-readable reports

---

## P2 — Repository ergonomics for AI maintenance

### P2-1 Agent contracts as enforceable repo rules
- [ ] move or confirm all role contracts under `agents/`
- [ ] add scripts that verify generated vs hand-edited boundaries
- [ ] add `make validate-local` / `make replay` / `make eval` / `make release-check`

### P2-2 State root hygiene
- [ ] ensure active tasks, indexes, ledgers, backups never write into code root
- [ ] add bootstrap command to create state root
- [ ] add cleanup/archive commands

### P2-3 Migration discipline
- [ ] add migration command skeletons for artifact schema and thin-KB schema changes
- [ ] add migration smoke tests

Acceptance:
- a maintenance agent can discover, validate, and execute the expected workflow from the repo itself

---

## P3 — Operational safety

### P3-1 Backup and restore
- [ ] implement backup command for tasks, KB, indexes, ledgers
- [ ] implement restore command
- [ ] add restore drill test in CI or scheduled maintenance run

### P3-2 Observability
- [ ] structured logs with `task_id`, `request_id`, `trace_id`
- [ ] health endpoints for every service
- [ ] simple metrics export or periodic reports for latency, error counts, replay/eval trends

### P3-3 Security and isolation tests
- [ ] unauthorized write tests
- [ ] cross-task isolation tests
- [ ] memory scope leak tests
- [ ] adapter token misuse tests

Acceptance:
- failures can be diagnosed without manual guesswork

---

## P4 — Optional after stabilization

### P4-1 Smarter memory
- [ ] evaluate Mem0 graph memory only after replay/eval are stable
- [ ] add memory quality checks before enabling richer memory graphs

### P4-2 Retrieval upgrade
- [ ] add LanceDB hybrid retrieval only after SQLite FTS baseline is measured and replayed
- [ ] compare against current exact/fts path before replacing it

### P4-3 Parsing pipeline
- [ ] add Docling and Tree-sitter only when ingest volume and manual extraction pain justify it
