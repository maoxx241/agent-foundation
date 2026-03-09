from __future__ import annotations

import pytest

from tests.helpers import (
    create_task,
    get_state,
    make_artifact_client,
    patch_state,
    put_json,
    put_markdown,
    put_text,
    reach_evidence_ready,
)


WORKFLOW_CASES = [
    ("W-01", "reject", False, "reject", False, False, "EVIDENCE_READY"),
    ("W-02", "reject", False, "approve", True, True, "EVIDENCE_READY"),
    ("W-03", "reject", True, "reject", True, True, "EVIDENCE_READY"),
    ("W-04", "reject", True, "approve", False, False, "EVIDENCE_READY"),
    ("W-05", "approve", False, "reject", True, False, "DESIGN_APPROVED"),
    ("W-06", "approve", False, "approve", False, False, "DESIGN_APPROVED"),
    ("W-07", "approve", True, "reject", False, False, "IMPLEMENTED"),
    ("W-08", "approve", True, "approve", True, True, "WRITTEN_BACK"),
]


@pytest.mark.parametrize(
    ("case_id", "design_verdict", "valid_test_plan", "impl_verdict", "validation_pass", "writeback_eligible", "expected_state"),
    WORKFLOW_CASES,
)
def test_workflow_matrix(
    tmp_path,
    case_id: str,
    design_verdict: str,
    valid_test_plan: bool,
    impl_verdict: str,
    validation_pass: bool,
    writeback_eligible: bool,
    expected_state: str,
):
    client = make_artifact_client(tmp_path)
    task_id = case_id.lower()
    create_task(client, task_id)
    reach_evidence_ready(client, task_id)

    put_json(client, task_id, "20_design", "design-spec.json", {"objective": "implement", "selected_option": "A"})
    put_json(client, task_id, "20_design", "design-review.json", {"verdict": design_verdict})
    response = patch_state(client, task_id, "DESIGN_APPROVED", "review")
    if design_verdict != "approve":
        assert response.status_code == 409
        assert get_state(client, task_id) == expected_state
        return
    assert response.status_code == 200

    if valid_test_plan:
        put_json(client, task_id, "30_test", "test-spec.json", {"strategy_summary": "valid"})
        put_json(client, task_id, "30_test", "acceptance.json", {"criteria": ["pass"]})
    else:
        put_json(client, task_id, "30_test", "test-spec.json", {"strategy_summary": "missing acceptance"})

    response = patch_state(client, task_id, "TESTSPEC_FROZEN", "qa")
    if not valid_test_plan:
        assert response.status_code == 409
        assert get_state(client, task_id) == expected_state
        return
    assert response.status_code == 200

    put_text(client, task_id, "40_dev", "patch.diff", "diff --git a/a.py b/a.py")
    put_json(client, task_id, "40_dev", "changed-files.json", ["a.py"])
    put_json(client, task_id, "40_dev", "selftest.json", {"passed": True, "summary": "green"})
    response = patch_state(client, task_id, "IMPLEMENTED", "engineer")
    assert response.status_code == 200

    put_json(client, task_id, "50_review", "impl-review.json", {"verdict": impl_verdict})
    response = patch_state(client, task_id, "IMPL_APPROVED", "review")
    if impl_verdict != "approve":
        assert response.status_code == 409
        assert get_state(client, task_id) == expected_state
        return
    assert response.status_code == 200

    put_json(
        client,
        task_id,
        "60_validation",
        "validation-report.json",
        {"passed": validation_pass, "summary": "validation"},
    )
    put_json(client, task_id, "60_validation", "regression.json", {"status": "clean"})
    response = patch_state(client, task_id, "VALIDATED", "qa")
    if not validation_pass:
        assert response.status_code == 409
        assert get_state(client, task_id) == "IMPL_APPROVED"
        return
    assert response.status_code == 200

    if not writeback_eligible:
        assert get_state(client, task_id) == "VALIDATED"
        return

    put_json(client, task_id, "70_release", "adr.json", {"title": "ADR", "context": "ctx", "decision": "ship"})
    put_markdown(client, task_id, "70_release", "changelog.md", "# Changelog")
    response = patch_state(client, task_id, "RELEASED", "release")
    assert response.status_code == 200
    put_json(
        client,
        task_id,
        "80_writeback",
        "experience-packet.json",
        {"project_id": "proj", "summary": "summary", "validation_summary": "green"},
    )
    response = client.post(f"/v1/tasks/{task_id}/experience/finalize")
    assert response.status_code == 200
    assert get_state(client, task_id) == expected_state

