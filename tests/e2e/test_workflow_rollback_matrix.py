from __future__ import annotations

import pytest

from tests.helpers import (
    create_task,
    get_state,
    make_artifact_client,
    patch_state,
    put_json,
    put_markdown,
    reach_design_approved,
    reach_impl_approved,
    reach_testspec_frozen,
    reach_validated,
    reach_written_back,
)


def reach_released(client, task_id: str) -> None:
    reach_validated(client, task_id, full=True)
    put_json(client, task_id, "70_release", "adr.json", {"title": "ADR", "context": "ctx", "decision": "ship"})
    put_markdown(client, task_id, "70_release", "changelog.md", "# Changelog")
    response = patch_state(client, task_id, "RELEASED", "release")
    assert response.status_code == 200, response.text


ROLLBACK_CASES = [
    ("W-RB-01", reach_design_approved, "EVIDENCE_READY"),
    ("W-RB-02", reach_testspec_frozen, "DESIGN_APPROVED"),
    ("W-RB-03", reach_impl_approved, "IMPLEMENTED"),
    ("W-RB-04", reach_validated, "DESIGN_APPROVED"),
    ("W-RB-05", reach_released, "VALIDATED"),
    ("W-RB-06", reach_written_back, "IMPLEMENTED"),
]


@pytest.mark.parametrize(("task_id", "setup", "target_state"), ROLLBACK_CASES)
def test_documented_rollbacks_are_allowed(tmp_path, task_id: str, setup, target_state: str):
    client = make_artifact_client(tmp_path)
    create_task(client, task_id.lower())
    setup(client, task_id.lower(), full=True) if setup is not reach_released else setup(client, task_id.lower())

    response = patch_state(client, task_id.lower(), target_state, "qa")
    assert response.status_code == 200, response.text
    assert get_state(client, task_id.lower()) == target_state


@pytest.mark.parametrize(
    ("classification", "expected_hint"),
    [
        ("implementation_defect", "IMPLEMENTED"),
        ("design_ambiguity", "DESIGN_APPROVED"),
        ("testspec_weakness", "TESTSPEC_FROZEN"),
    ],
)
def test_validation_failure_hints_match_root_cause(tmp_path, classification: str, expected_hint: str):
    client = make_artifact_client(tmp_path)
    task_id = f"task-{classification}"
    create_task(client, task_id)
    reach_impl_approved(client, task_id, full=True)
    put_json(
        client,
        task_id,
        "60_validation",
        "validation-report.json",
        {
            "passed": False,
            "summary": "validation failed",
            "root_cause_classification": classification,
        },
    )
    put_json(client, task_id, "60_validation", "regression.json", {"status": "failed"})

    response = patch_state(client, task_id, "VALIDATED", "qa")
    assert response.status_code == 409
    assert expected_hint in response.json()["detail"]
