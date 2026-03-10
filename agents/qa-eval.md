# QA Eval

- Run `pytest -q` before handoff.
- Regenerate contracts with `python scripts/generate_contract_artifacts.py` after OpenAPI or schema changes.
- Cover replay, retrieval, auth, and audit surfaces when writeback or storage behavior changes.
- Treat contract drift and missing ledger events as release blockers.
