from __future__ import annotations

import pytest
from schemathesis import openapi

from apps.artifact_api.main import create_app as create_artifact_app
from apps.thin_kb_api.main import create_app as create_kb_app
from libs.storage.artifact_store import ArtifactStore
from libs.storage.thin_kb_store import ThinKBStore

pytestmark = [
    pytest.mark.filterwarnings("ignore:The `.example()` method is good for exploring strategies*:hypothesis.errors.NonInteractiveExampleWarning"),
    pytest.mark.filterwarnings("ignore:jsonschema.exceptions.RefResolutionError is deprecated*:DeprecationWarning"),
]


def test_artifact_openapi_schemathesis_smoke(tmp_path):
    app = create_artifact_app(ArtifactStore(tmp_path / "tasks"))
    schema = openapi.from_asgi("/openapi.json", app)
    operation = schema.find_operation_by_label("POST /v1/tasks")
    case = operation.as_strategy().example()
    case.body = {
        "task_id": "contract-task",
        "project_id": "contract-proj",
        "title": "contract-title",
        "goal": "contract-goal",
    }
    response = case.call(base_url="http://testserver")
    case.validate_response(response)
    assert response.status_code < 500

    invalid_case = operation.as_strategy().example()
    invalid_case.body = {"task_id": "only-one-field"}
    invalid_response = invalid_case.call(base_url="http://testserver")
    assert invalid_response.status_code == 422


def test_thin_kb_openapi_schemathesis_smoke(tmp_path):
    app = create_kb_app(ThinKBStore(tmp_path / "kb", tmp_path / "kb" / "manifest.sqlite3"))
    schema = openapi.from_asgi("/openapi.json", app)
    operation = schema.find_operation_by_label("POST /v1/kb/search")
    case = operation.as_strategy().example()
    case.body = {"query": "contract"}
    response = case.call(base_url="http://testserver")
    case.validate_response(response)
    assert response.status_code < 500

    invalid_case = operation.as_strategy().example()
    invalid_case.body = {"limit": -1, "query": []}
    invalid_response = invalid_case.call(base_url="http://testserver")
    assert invalid_response.status_code == 422
