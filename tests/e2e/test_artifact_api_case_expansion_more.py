from __future__ import annotations

from tests.helpers import (
    create_task,
    make_artifact_client,
    patch_state,
    put_json,
    put_markdown,
    reach_design_approved,
    reach_validated,
)


def _reach_released(client, task_id: str) -> None:
    reach_validated(client, task_id, full=True)
    put_json(client, task_id, "70_release", "adr.json", {"title": "ADR", "context": "ctx", "decision": "ship"})
    put_markdown(client, task_id, "70_release", "changelog.md", "# Changelog\n\n- released")
    response = patch_state(client, task_id, "RELEASED", "release")
    assert response.status_code == 200, response.text


def test_a03_missing_artifact_file_returns_404(tmp_path):
    client = make_artifact_client(tmp_path)
    create_task(client, "task-missing-artifact")

    response = client.get("/v1/tasks/task-missing-artifact/artifacts/10_evidence/evidence-pack.json")
    assert response.status_code == 404


def test_a04_format_mismatch_is_rejected(tmp_path):
    client = make_artifact_client(tmp_path)
    create_task(client, "task-format-mismatch")

    response = client.put(
        "/v1/tasks/task-format-mismatch/artifacts/10_evidence/evidence-pack.json",
        json={"format": "markdown", "content": "not-json"},
    )
    assert response.status_code == 422


def test_a06_bad_schema_payload_is_rejected_for_enum_field(tmp_path):
    client = make_artifact_client(tmp_path)
    create_task(client, "task-bad-review")
    reach_design_approved(client, "task-bad-review", full=True)

    response = client.put(
        "/v1/tasks/task-bad-review/artifacts/50_review/impl-review.json",
        json={"format": "json", "content": {"verdict": "not-a-verdict"}},
    )
    assert response.status_code == 422


def test_a07_artifact_list_reports_format_and_size(tmp_path):
    client = make_artifact_client(tmp_path)
    create_task(client, "task-list-shape")
    put_markdown(client, "task-list-shape", "70_release", "changelog.md", "# Changelog\n\n- item")

    response = client.get("/v1/tasks/task-list-shape/artifacts")
    assert response.status_code == 200
    entry = response.json()["artifacts"]["70_release"][0]
    assert entry["name"] == "changelog.md"
    assert entry["format"] == "markdown"
    assert entry["size_bytes"] > 0


def test_a11_finalize_after_release_creates_finalization_marker(tmp_path):
    client = make_artifact_client(tmp_path)
    create_task(client, "task-finalize-success")
    _reach_released(client, "task-finalize-success")
    put_json(
        client,
        "task-finalize-success",
        "80_writeback",
        "experience-packet.json",
        {"project_id": "proj", "summary": "summary", "validation_summary": "green"},
    )

    response = client.post("/v1/tasks/task-finalize-success/experience/finalize")
    assert response.status_code == 200

    response = client.get("/v1/tasks/task-finalize-success/artifacts/80_writeback/finalization.json")
    assert response.status_code == 200
    assert response.json()["content"]["finalized_by"] == "artifact_api"


def test_a14_bundle_reflects_partial_progress_state(tmp_path):
    client = make_artifact_client(tmp_path)
    create_task(client, "task-partial-bundle")
    reach_design_approved(client, "task-partial-bundle", full=True)

    response = client.get("/v1/tasks/task-partial-bundle/bundle")
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "DESIGN_APPROVED"
    assert any(item["stage"] == "20_design" and item["name"] == "design-spec.json" for item in payload["artifacts"])
