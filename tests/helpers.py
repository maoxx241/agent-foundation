from __future__ import annotations

from fastapi.testclient import TestClient

from apps.artifact_api.main import create_app as create_artifact_app
from apps.thin_kb_api.main import create_app as create_kb_app
from packages.core.storage.artifact_store import ArtifactStore
from packages.core.storage.thin_kb_store import ThinKBStore

AGENT_HEADERS = {"x-service-token": "agent-token"}
OPERATOR_HEADERS = {"x-service-token": "operator-token"}


def make_artifact_client(tmp_path) -> TestClient:
    store = ArtifactStore(tmp_path / "tasks")
    return TestClient(create_artifact_app(store), headers=AGENT_HEADERS)


def create_task(client: TestClient, task_id: str) -> None:
    response = client.post(
        "/v1/tasks",
        json={
            "task_id": task_id,
            "project_id": "proj",
            "title": task_id,
            "goal": "exercise workflow",
        },
    )
    assert response.status_code == 200, response.text


def put_json(client: TestClient, task_id: str, stage: str, name: str, content) -> None:
    response = client.put(
        f"/v1/tasks/{task_id}/artifacts/{stage}/{name}",
        json={"format": "json", "content": content},
    )
    assert response.status_code == 200, response.text


def put_markdown(client: TestClient, task_id: str, stage: str, name: str, content: str) -> None:
    response = client.put(
        f"/v1/tasks/{task_id}/artifacts/{stage}/{name}",
        json={"format": "markdown", "content": content},
    )
    assert response.status_code == 200, response.text


def put_text(client: TestClient, task_id: str, stage: str, name: str, content: str) -> None:
    response = client.put(
        f"/v1/tasks/{task_id}/artifacts/{stage}/{name}",
        json={"format": "text", "content": content},
    )
    assert response.status_code == 200, response.text


def patch_state(client: TestClient, task_id: str, state: str, changed_by: str = "tester"):
    return client.patch(
        f"/v1/tasks/{task_id}/state",
        json={"target_state": state, "changed_by": changed_by},
    )


def get_state(client: TestClient, task_id: str) -> str:
    response = client.get(f"/v1/tasks/{task_id}")
    assert response.status_code == 200, response.text
    return response.json()["state"]["state"]


def reach_evidence_ready(client: TestClient, task_id: str, full: bool = False) -> None:
    payload = {
        "summary": "evidence summary",
    }
    if full:
        payload.update(
            {
                "claims": ["claim-a"],
                "constraints": ["constraint-a"],
                "risks": ["risk-a"],
                "gaps": ["gap-a"],
            }
        )
    put_json(client, task_id, "10_evidence", "evidence-pack.json", payload)
    response = patch_state(client, task_id, "EVIDENCE_READY", "lead")
    assert response.status_code == 200, response.text


def reach_design_approved(client: TestClient, task_id: str, full: bool = False, verdict: str = "approve") -> None:
    reach_evidence_ready(client, task_id, full=full)
    payload = {
        "objective": "implement the workflow",
        "selected_option": "Option A",
    }
    if full:
        payload.update(
            {
                "constraints": ["stay file-first"],
                "assumptions": ["local disk available"],
                "invariants": ["no illegal transition"],
            }
        )
    put_json(client, task_id, "20_design", "design-spec.json", payload)
    review = {"verdict": verdict}
    if full and verdict == "approve":
        review["minor_issues"] = ["document follow-up"]
    put_json(client, task_id, "20_design", "design-review.json", review)
    response = patch_state(client, task_id, "DESIGN_APPROVED", "review")
    assert response.status_code == 200, response.text


def reach_testspec_frozen(client: TestClient, task_id: str, full: bool = False) -> None:
    reach_design_approved(client, task_id, full=full)
    test_spec = {"strategy_summary": "cover the happy path"}
    if full:
        test_spec.update(
            {
                "invariants": ["state gates are enforced"],
                "acceptance_criteria": ["task advances only with required artifacts"],
            }
        )
    put_json(client, task_id, "30_test", "test-spec.json", test_spec)
    put_json(client, task_id, "30_test", "acceptance.json", {"criteria": ["works"]})
    response = patch_state(client, task_id, "TESTSPEC_FROZEN", "qa")
    assert response.status_code == 200, response.text


def reach_implemented(client: TestClient, task_id: str, full: bool = False) -> None:
    reach_testspec_frozen(client, task_id, full=full)
    put_text(client, task_id, "40_dev", "patch.diff", "diff --git a/file.py b/file.py")
    put_json(client, task_id, "40_dev", "changed-files.json", ["file.py"])
    selftest = {"passed": True, "summary": "self tests green"}
    if full:
        selftest["commands_run"] = ["pytest -q", "ruff check ."]
    put_json(client, task_id, "40_dev", "selftest.json", selftest)
    response = patch_state(client, task_id, "IMPLEMENTED", "engineer")
    assert response.status_code == 200, response.text


def reach_impl_approved(client: TestClient, task_id: str, full: bool = False) -> None:
    reach_implemented(client, task_id, full=full)
    review = {"verdict": "approve"}
    if full:
        review["implementation_risks"] = ["watch follow-up cleanup"]
    put_json(client, task_id, "50_review", "impl-review.json", review)
    response = patch_state(client, task_id, "IMPL_APPROVED", "review")
    assert response.status_code == 200, response.text


def reach_validated(client: TestClient, task_id: str, full: bool = False) -> None:
    reach_impl_approved(client, task_id, full=full)
    report = {"passed": True, "summary": "validation passed"}
    if full:
        report.update({"functional_result": "pass", "regression_result": "pass"})
    put_json(client, task_id, "60_validation", "validation-report.json", report)
    put_json(client, task_id, "60_validation", "regression.json", {"status": "clean"})
    put_json(client, task_id, "60_validation", "perf.json", {"status": "n/a"})
    response = patch_state(client, task_id, "VALIDATED", "qa")
    assert response.status_code == 200, response.text


def reach_written_back(client: TestClient, task_id: str, full: bool = False) -> None:
    reach_validated(client, task_id, full=full)
    adr = {"title": "ADR", "context": "ctx", "decision": "ship it"}
    if full:
        adr["tradeoffs"] = ["keeps phase 1 small"]
    put_json(client, task_id, "70_release", "adr.json", adr)
    put_markdown(client, task_id, "70_release", "changelog.md", "# Changelog\n\n- released")
    response = patch_state(client, task_id, "RELEASED", "release")
    assert response.status_code == 200, response.text
    experience = {
        "project_id": "proj",
        "summary": "experience summary",
        "validation_summary": "all green",
    }
    if full:
        experience["candidate_claims"] = ["phase1 uses sqlite fts5"]
    put_json(client, task_id, "80_writeback", "experience-packet.json", experience)
    response = client.post(f"/v1/tasks/{task_id}/experience/finalize")
    assert response.status_code == 200, response.text


def make_kb_client(tmp_path) -> TestClient:
    store = ThinKBStore(tmp_path / "kb", tmp_path / "kb" / "manifest.sqlite3")
    store.upsert(
        {
            "id": "claim-trusted",
            "object_type": "claim",
            "title": "Phase 1 uses SQLite FTS5",
            "summary": "Trusted claim for exact lookup",
            "subject": "phase1",
            "predicate": "uses",
            "statement": "Phase 1 uses SQLite FTS5",
            "status": "trusted",
            "version": "1.0.0",
            "domain_tags": ["sqlite", "fts"],
        }
    )
    store.upsert(
        {
            "id": "procedure-candidate",
            "object_type": "procedure",
            "title": "Rollback the local index",
            "summary": "Restore a snapshot and rebuild the index",
            "goal": "Recover search",
            "steps": ["stop writes", "restore snapshot", "rebuild index"],
            "expected_outcomes": ["search recovers"],
            "status": "candidate",
            "version": "2.0.0",
            "domain_tags": ["ops", "recovery"],
        }
    )
    store.upsert(
        {
            "id": "decision-versioned",
            "object_type": "decision",
            "title": "Use versioned search filters",
            "summary": "Support version-aware lookups",
            "context": "Need version conditioning in Thin KB",
            "decision": "Expose an optional version filter",
            "status": "candidate",
            "version": "3.1.0",
            "domain_tags": ["api"],
        }
    )
    store.upsert(
        {
            "id": "claim-deprecated",
            "object_type": "claim",
            "title": "Legacy claim",
            "summary": "Deprecated historical fact",
            "subject": "legacy",
            "predicate": "used",
            "statement": "Legacy claim",
            "status": "deprecated",
            "version": "0.9.0",
            "domain_tags": ["legacy"],
        }
    )
    return TestClient(create_kb_app(store), headers=AGENT_HEADERS)
