from __future__ import annotations

import pytest

from packages.core.config import (
    DEFAULT_AGENT_SERVICE_TOKEN,
    DEFAULT_OPERATOR_SERVICE_TOKEN,
    agent_token,
    operator_token,
    validate_service_tokens,
)


def test_validate_service_tokens_requires_explicit_env(monkeypatch):
    monkeypatch.delenv("AGENT_FOUNDATION_AGENT_TOKEN", raising=False)
    monkeypatch.delenv("AGENT_FOUNDATION_OPERATOR_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="AGENT_FOUNDATION_AGENT_TOKEN"):
        validate_service_tokens()


def test_embedded_mode_can_opt_in_to_insecure_default_tokens(monkeypatch):
    monkeypatch.delenv("AGENT_FOUNDATION_AGENT_TOKEN", raising=False)
    monkeypatch.delenv("AGENT_FOUNDATION_OPERATOR_TOKEN", raising=False)

    assert agent_token(allow_insecure_default=True) == DEFAULT_AGENT_SERVICE_TOKEN
    assert operator_token(allow_insecure_default=True) == DEFAULT_OPERATOR_SERVICE_TOKEN
