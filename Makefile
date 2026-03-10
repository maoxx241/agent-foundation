PYTHON ?= .venv/bin/python
PYTEST ?= .venv/bin/pytest
RELEASE_CHECK_PROFILE ?= smoke

.PHONY: test contracts contracts-drift migrate-state plugin-check validate-local replay eval release-check bootstrap-runtime cleanup-runtime

test:
	$(PYTEST) -q

contracts:
	$(PYTHON) scripts/generate_contract_artifacts.py

contracts-drift:
	$(PYTHON) scripts/generate_contract_artifacts.py
	$(PYTHON) scripts/check_contract_drift.py

migrate-state:
	$(PYTHON) scripts/migrate_runtime_state.py

plugin-check:
	cd openclaw/plugin_adapter && npm run check && npm test

bootstrap-runtime:
	$(PYTHON) -m apps.cli.main bootstrap-runtime

cleanup-runtime:
	$(PYTHON) -m apps.cli.main cleanup-runtime

replay:
	$(PYTHON) -m apps.cli.main replay

eval:
	$(PYTHON) -m apps.cli.main eval

release-check:
	$(PYTHON) -m apps.cli.main release-check --profile $(RELEASE_CHECK_PROFILE)

validate-local: contracts-drift test release-check
