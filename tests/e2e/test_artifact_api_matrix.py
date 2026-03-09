from __future__ import annotations

import pytest

from tests.helpers import (
    create_task,
    get_state,
    make_artifact_client,
    patch_state,
    put_json,
    reach_design_approved,
    reach_evidence_ready,
    reach_validated,
)


def reach_released(client, task_id: str, full: bool = False) -> None:
    reach_validated(client, task_id, full=full)
    put_json(client, task_id, "70_release", "adr.json", {"title": "ADR", "context": "ctx", "decision": "ship"})
    response = client.put(
        f"/v1/tasks/{task_id}/artifacts/70_release/changelog.md",
        json={"format": "markdown", "content": "# Changelog\n\n- released"},
    )
    assert response.status_code == 200, response.text
    response = patch_state(client, task_id, "RELEASED", "release")
    assert response.status_code == 200, response.text


def case_a01(client, task_id: str):
    reach_evidence_ready(client, task_id, full=False)
    response = client.get(f"/v1/tasks/{task_id}")
    assert response.status_code == 200


def case_a02(client, task_id: str):
    put_json(
        client,
        task_id,
        "10_evidence",
        "evidence-pack.json",
        {"summary": "full evidence", "claims": ["a"], "constraints": ["b"], "risks": ["c"], "gaps": ["d"]},
    )
    put_json(client, task_id, "10_evidence", "evidence-pack.json", {"summary": "overwritten evidence", "claims": ["a"]})
    response = patch_state(client, task_id, "DESIGN_APPROVED", "lead")
    assert response.status_code == 409
    assert "Illegal transition" in response.json()["detail"]


def case_a03(client, task_id: str):
    response = client.put(
        f"/v1/tasks/{task_id}/artifacts/10_evidence/evidence-pack.json",
        json={"format": "json", "content": {"claims": ["missing summary"]}},
    )
    assert response.status_code == 422


def case_a04(client, task_id: str):
    reach_design_approved(client, task_id, full=False)
    put_json(client, task_id, "30_test", "test-spec.json", {"strategy_summary": "minimal"})
    response = patch_state(client, task_id, "TESTSPEC_FROZEN", "qa")
    assert response.status_code == 409
    assert "acceptance.json" in response.json()["detail"]


def case_a05(client, task_id: str):
    reach_design_approved(client, task_id, full=True)
    response = patch_state(client, task_id, "NEW", "qa")
    assert response.status_code == 409
    assert "Illegal transition" in response.json()["detail"]


def case_a06(client, task_id: str):
    reach_evidence_ready(client, task_id, full=True)
    put_json(client, task_id, "30_test", "test-spec.json", {"strategy_summary": "valid first write"})
    response = client.put(
        f"/v1/tasks/{task_id}/artifacts/30_test/test-spec.json",
        json={"format": "json", "content": {"acceptance_criteria": ["missing strategy_summary"]}},
    )
    assert response.status_code == 422


def case_a07(client, task_id: str):
    reach_validated(client, task_id, full=False)
    put_json(client, task_id, "60_validation", "regression.json", {"status": "overwritten"})
    response = patch_state(client, task_id, "NEW", "qa")
    assert response.status_code == 409
    assert "Illegal transition" in response.json()["detail"]


def case_a08(client, task_id: str):
    reach_released(client, task_id, full=True)
    response = client.post(f"/v1/tasks/{task_id}/experience/finalize")
    assert response.status_code == 409
    assert "experience-packet.json" in response.json()["detail"]


def case_a09(client, task_id: str):
    reach_released(client, task_id, full=False)
    response = client.put(
        f"/v1/tasks/{task_id}/artifacts/80_writeback/experience-packet.json",
        json={"format": "json", "content": {"summary": "missing required fields"}},
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("case_id", "runner"),
    [
        ("A-01", case_a01),
        ("A-02", case_a02),
        ("A-03", case_a03),
        ("A-04", case_a04),
        ("A-05", case_a05),
        ("A-06", case_a06),
        ("A-07", case_a07),
        ("A-08", case_a08),
        ("A-09", case_a09),
    ],
)
def test_artifact_api_orthogonal_matrix(tmp_path, case_id: str, runner):
    client = make_artifact_client(tmp_path)
    task_id = case_id.lower()
    create_task(client, task_id)
    runner(client, task_id)
    assert get_state(client, task_id) in {
        "NEW",
        "EVIDENCE_READY",
        "DESIGN_APPROVED",
        "TESTSPEC_FROZEN",
        "IMPLEMENTED",
        "IMPL_APPROVED",
        "VALIDATED",
        "RELEASED",
        "WRITTEN_BACK",
    }
