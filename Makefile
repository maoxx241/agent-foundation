PYTHON ?= .venv/bin/python
PYTEST ?= .venv/bin/pytest

.PHONY: test contracts migrate-state plugin-check

test:
	$(PYTEST) -q

contracts:
	$(PYTHON) scripts/generate_contract_artifacts.py

migrate-state:
	$(PYTHON) scripts/migrate_runtime_state.py

plugin-check:
	cd openclaw/plugin_adapter && npm test
