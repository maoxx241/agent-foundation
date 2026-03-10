from __future__ import annotations

from fastapi.testclient import TestClient

from apps.artifact_api.main import create_app
from packages.core.storage.artifact_store import ArtifactStore
from tests.helpers import AGENT_HEADERS


def make_client(tmp_path):
    store = ArtifactStore(tmp_path / "tasks")
    app = create_app(store)
    return TestClient(app, headers=AGENT_HEADERS)


def test_artifact_api_health_and_ready(tmp_path):
    client = make_client(tmp_path)
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").json() == {"status": "ready"}


def test_artifact_api_happy_path_to_written_back(tmp_path):
    client = make_client(tmp_path)
    task_id = "task-happy"

    response = client.post(
        "/v1/tasks",
        json={
            "task_id": task_id,
            "project_id": "proj",
            "title": "Happy path",
            "goal": "Walk through all states",
        },
    )
    assert response.status_code == 200
    assert response.json()["state"]["state"] == "NEW"

    client.put(
        f"/v1/tasks/{task_id}/artifacts/10_evidence/evidence-pack.json",
        json={"format": "json", "content": {"summary": "evidence summary"}},
    )
    response = client.patch(
        f"/v1/tasks/{task_id}/state",
        json={"target_state": "EVIDENCE_READY", "changed_by": "lead"},
    )
    assert response.status_code == 200
    assert response.json()["state"]["state"] == "EVIDENCE_READY"

    client.put(
        f"/v1/tasks/{task_id}/artifacts/20_design/design-spec.json",
        json={"format": "json", "content": {"objective": "implement", "selected_option": "A"}},
    )
    client.put(
        f"/v1/tasks/{task_id}/artifacts/20_design/design-review.json",
        json={"format": "json", "content": {"verdict": "approve"}},
    )
    response = client.patch(
        f"/v1/tasks/{task_id}/state",
        json={"target_state": "DESIGN_APPROVED", "changed_by": "review"},
    )
    assert response.status_code == 200

    client.put(
        f"/v1/tasks/{task_id}/artifacts/30_test/test-spec.json",
        json={"format": "json", "content": {"strategy_summary": "cover happy path"}},
    )
    client.put(
        f"/v1/tasks/{task_id}/artifacts/30_test/acceptance.json",
        json={"format": "json", "content": {"criteria": ["works"]}},
    )
    response = client.patch(
        f"/v1/tasks/{task_id}/state",
        json={"target_state": "TESTSPEC_FROZEN", "changed_by": "qa"},
    )
    assert response.status_code == 200

    client.put(
        f"/v1/tasks/{task_id}/artifacts/40_dev/patch.diff",
        json={"format": "text", "content": "diff --git a/file b/file"},
    )
    client.put(
        f"/v1/tasks/{task_id}/artifacts/40_dev/changed-files.json",
        json={"format": "json", "content": ["file.py"]},
    )
    client.put(
        f"/v1/tasks/{task_id}/artifacts/40_dev/selftest.json",
        json={"format": "json", "content": {"passed": True, "summary": "self test passed"}},
    )
    response = client.patch(
        f"/v1/tasks/{task_id}/state",
        json={"target_state": "IMPLEMENTED", "changed_by": "engineer"},
    )
    assert response.status_code == 200

    client.put(
        f"/v1/tasks/{task_id}/artifacts/50_review/impl-review.json",
        json={"format": "json", "content": {"verdict": "approve"}},
    )
    response = client.patch(
        f"/v1/tasks/{task_id}/state",
        json={"target_state": "IMPL_APPROVED", "changed_by": "review"},
    )
    assert response.status_code == 200

    client.put(
        f"/v1/tasks/{task_id}/artifacts/60_validation/validation-report.json",
        json={"format": "json", "content": {"passed": True, "summary": "validation passed"}},
    )
    client.put(
        f"/v1/tasks/{task_id}/artifacts/60_validation/regression.json",
        json={"format": "json", "content": {"status": "clean"}},
    )
    client.put(
        f"/v1/tasks/{task_id}/artifacts/60_validation/perf.json",
        json={"format": "json", "content": {"status": "n/a"}},
    )
    response = client.patch(
        f"/v1/tasks/{task_id}/state",
        json={"target_state": "VALIDATED", "changed_by": "qa"},
    )
    assert response.status_code == 200

    client.put(
        f"/v1/tasks/{task_id}/artifacts/70_release/adr.json",
        json={"format": "json", "content": {"title": "ADR", "context": "ctx", "decision": "ship it"}},
    )
    client.put(
        f"/v1/tasks/{task_id}/artifacts/70_release/changelog.md",
        json={"format": "markdown", "content": "# Changelog\n\n- released"},
    )
    response = client.patch(
        f"/v1/tasks/{task_id}/state",
        json={"target_state": "RELEASED", "changed_by": "release"},
    )
    assert response.status_code == 200

    client.put(
        f"/v1/tasks/{task_id}/artifacts/80_writeback/experience-packet.json",
        json={
            "format": "json",
            "content": {
                "project_id": "proj",
                "summary": "experience summary",
                "validation_summary": "green",
            },
        },
    )
    response = client.post(f"/v1/tasks/{task_id}/experience/finalize")
    assert response.status_code == 200
    assert response.json()["state"] == "WRITTEN_BACK"

    response = client.get(f"/v1/tasks/{task_id}/bundle")
    assert response.status_code == 200
    assert response.json()["state"] == "WRITTEN_BACK"


def test_artifact_api_blocks_transition_without_testspec(tmp_path):
    client = make_client(tmp_path)
    task_id = "task-blocked"

    client.post(
        "/v1/tasks",
        json={
            "task_id": task_id,
            "project_id": "proj",
            "title": "Blocked path",
            "goal": "Ensure illegal transition fails",
        },
    )
    client.put(
        f"/v1/tasks/{task_id}/artifacts/10_evidence/evidence-pack.json",
        json={"format": "json", "content": {"summary": "evidence summary"}},
    )
    client.patch(
        f"/v1/tasks/{task_id}/state",
        json={"target_state": "EVIDENCE_READY", "changed_by": "lead"},
    )
    client.put(
        f"/v1/tasks/{task_id}/artifacts/20_design/design-spec.json",
        json={"format": "json", "content": {"objective": "implement", "selected_option": "A"}},
    )
    client.put(
        f"/v1/tasks/{task_id}/artifacts/20_design/design-review.json",
        json={"format": "json", "content": {"verdict": "approve"}},
    )
    client.patch(
        f"/v1/tasks/{task_id}/state",
        json={"target_state": "DESIGN_APPROVED", "changed_by": "review"},
    )

    response = client.patch(
        f"/v1/tasks/{task_id}/state",
        json={"target_state": "IMPLEMENTED", "changed_by": "engineer"},
    )
    assert response.status_code == 409
    assert "Illegal transition" in response.json()["detail"]


def test_finalize_is_blocked_before_validated(tmp_path):
    client = make_client(tmp_path)
    task_id = "task-finalize-blocked"

    client.post(
        "/v1/tasks",
        json={
            "task_id": task_id,
            "project_id": "proj",
            "title": "Finalize guard",
            "goal": "Cannot finalize early",
        },
    )
    client.put(
        f"/v1/tasks/{task_id}/artifacts/80_writeback/experience-packet.json",
        json={
            "format": "json",
            "content": {
                "project_id": "proj",
                "summary": "summary",
                "validation_summary": "pending",
            },
        },
    )
    response = client.post(f"/v1/tasks/{task_id}/experience/finalize")
    assert response.status_code == 409
    assert "before VALIDATED" in response.json()["detail"]
