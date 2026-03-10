from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from apps.artifact_api.main import create_app as create_artifact_app
from apps.thin_kb_api.main import create_app as create_kb_app
from packages.core.config import repo_root as default_repo_root
from packages.core.config import shadow_runs_root
from packages.core.observability import Observability
from packages.core.schemas import (
    EvalRun,
    GoldQueryCase,
    ReplayCase,
    ReplayCaseResult,
    ReplayStepResult,
    RetrievalCaseResult,
)
from packages.core.storage.artifact_store import ArtifactStore
from packages.core.storage.fs_utils import ensure_dir, utc_now
from packages.core.storage.phase2_store import Phase2Store
from packages.core.storage.thin_kb_store import ThinKBStore
from tests.helpers import AGENT_HEADERS
from .metrics import compute_retrieval_metrics, compute_workflow_metrics
from .reporting import new_run_id


class EvaluationRunner:
    def __init__(self, repo_root: Path | None = None, workspace_root: Path | None = None):
        self.repo_root = repo_root.resolve() if repo_root is not None else default_repo_root()
        if workspace_root is not None:
            self.workspace_root = workspace_root.resolve()
        elif repo_root is not None:
            self.workspace_root = (self.repo_root / "shadow_runs").resolve()
        else:
            self.workspace_root = shadow_runs_root()

    def run(
        self,
        *,
        gold_cases: list[GoldQueryCase],
        replay_cases: list[ReplayCase],
        run_id: str | None = None,
    ) -> EvalRun:
        run_id = run_id or new_run_id()
        retrieval_results = [self.run_gold_case(case, run_id=run_id) for case in gold_cases]
        replay_results = [self.run_replay_case(case, run_id=run_id) for case in replay_cases]
        generated_at = utc_now().isoformat()
        return EvalRun(
            run_id=run_id,
            generated_at=generated_at,
            retrieval_results=retrieval_results,
            replay_results=replay_results,
            retrieval_metrics=compute_retrieval_metrics(retrieval_results),
            workflow_metrics=compute_workflow_metrics(replay_results),
        )

    def run_gold_case(self, case: GoldQueryCase, *, run_id: str) -> RetrievalCaseResult:
        workspace_root = self.workspace_root / run_id / "gold" / case.case_id
        env = self._make_environment(workspace_root)
        try:
            self._seed_kb_defaults(env["kb_store"])
            response = env["kb_client"].post(
                "/v1/kb/search/hybrid",
                json={
                    "query": case.query,
                    "version": case.version,
                    "domain_tags": case.domain_tags,
                    "scope": case.scope,
                    "status": case.status_filter,
                    "limit": 10,
                },
                headers={"x-run-id": run_id},
            )
            payload = response.json()
            hits = payload.get("hits", []) if response.status_code == 200 else []
            actual_ids = [item["id"] for item in hits]
            top_hit = hits[0] if hits else {}
            return RetrievalCaseResult(
                case_id=case.case_id,
                expected_ids=case.expected_ids,
                actual_ids=actual_ids,
                requested_version=case.version,
                top_hit_version=(top_hit.get("metadata") or {}).get("version"),
                abstained=not hits,
                warnings=payload.get("warnings", []),
            )
        finally:
            env["artifact_client"].close()
            env["kb_client"].close()

    def run_replay_case(self, case: ReplayCase, *, run_id: str) -> ReplayCaseResult:
        workspace_root = self.workspace_root / run_id / "replay" / case.case_id
        env = self._make_environment(workspace_root)
        try:
            self._seed_case(case, env["artifact_client"], env["kb_store"], env["phase2_store"])
            step_results: list[ReplayStepResult] = []
            for step in case.steps:
                client = env["kb_client"] if "/v1/kb/" in step.path else env["artifact_client"]
                response = client.request(
                    step.method,
                    step.path,
                    json=step.body,
                    headers={"x-run-id": run_id},
                )
                body_excerpt = response.text[:240]
                state = None
                promoted_count = 0
                if response.headers.get("content-type", "").startswith("application/json"):
                    payload = response.json()
                    state = _extract_state(payload)
                    promoted_count = len(payload.get("object_ids", [])) if isinstance(payload, dict) else 0
                step_results.append(
                    ReplayStepResult(
                        method=step.method,
                        path=step.path,
                        status_code=response.status_code,
                        ok=response.status_code == step.expect_status,
                        target_state=(step.body or {}).get("target_state"),
                        state=state,
                        promoted_object_count=promoted_count,
                        body_excerpt=body_excerpt,
                    )
                )

            final_states = self._collect_final_states(case, env["artifact_client"])
            warnings = [
                warning
                for step_result, step in zip(step_results, case.steps)
                if not step_result.ok
                for warning in [f"{step.method} {step.path} expected {step.expect_status} got {step_result.status_code}"]
            ]
            ok = all(item.ok for item in step_results) and all(
                final_states.get(task_id) == state for task_id, state in case.expected.final_states.items()
            )
            return ReplayCaseResult(
                case_id=case.case_id,
                kind=case.kind,
                task_ids=[task.task_id for task in case.seed.tasks],
                ok=ok,
                final_states=final_states,
                steps=step_results,
                warnings=warnings,
            )
        finally:
            env["artifact_client"].close()
            env["kb_client"].close()

    def _make_environment(self, workspace_root: Path) -> dict[str, Any]:
        if workspace_root.exists():
            shutil.rmtree(workspace_root)
        tasks_root = workspace_root / "tasks"
        kb_root = workspace_root / "kb"
        observability_root = workspace_root / "observability"
        ensure_dir(tasks_root)
        ensure_dir(kb_root)
        artifact_store = ArtifactStore(tasks_root)
        kb_store = ThinKBStore(kb_root=kb_root, db_path=kb_root / "manifest.sqlite3")
        phase2_store = Phase2Store(kb_root=kb_root, db_path=kb_store.db_path, tasks_root=tasks_root, canonical_store=kb_store)
        artifact_client = TestClient(
            create_artifact_app(artifact_store, Observability(observability_root / "artifact_api")),
            headers=AGENT_HEADERS,
        )
        kb_client = TestClient(
            create_kb_app(kb_store, phase2_store, Observability(observability_root / "thin_kb_api")),
            headers=AGENT_HEADERS,
        )
        return {
            "artifact_client": artifact_client,
            "kb_client": kb_client,
            "artifact_store": artifact_store,
            "kb_store": kb_store,
            "phase2_store": phase2_store,
        }

    def _seed_kb_defaults(self, kb_store: ThinKBStore) -> None:
        for payload in (
            {
                "id": "claim-eval-fts",
                "object_type": "claim",
                "title": "Exact search stays important",
                "summary": "Hybrid retrieval complements exact search",
                "subject": "retrieval",
                "predicate": "uses",
                "statement": "Hybrid retrieval complements exact search",
                "status": "trusted",
                "version": "1.0.0",
                "domain_tags": ["retrieval"],
            },
            {
                "id": "procedure-eval-restore",
                "object_type": "procedure",
                "title": "Restore a snapshot",
                "summary": "Restore backup and rebuild the index",
                "goal": "Recover retrieval",
                "steps": ["restore backup", "rebuild index"],
                "expected_outcomes": ["retrieval restored"],
                "status": "trusted",
                "version": "1.0.0",
                "domain_tags": ["recovery"],
            },
        ):
            kb_store.upsert(payload)

    def _seed_case(
        self,
        case: ReplayCase,
        artifact_client: TestClient,
        kb_store: ThinKBStore,
        phase2_store: Phase2Store,
    ) -> None:
        for task in case.seed.tasks:
            response = artifact_client.post("/v1/tasks", json=task.model_dump(mode="json"))
            if response.status_code != 200:
                raise AssertionError(response.text)
        for artifact in case.seed.artifacts:
            response = artifact_client.put(
                f"/v1/tasks/{artifact.task_id}/artifacts/{artifact.stage}/{artifact.name}",
                json={"format": artifact.format, "content": artifact.content},
            )
            if response.status_code != 200:
                raise AssertionError(response.text)
        for payload in case.seed.kb_objects:
            kb_store.upsert(payload)
        for payload in case.seed.documents:
            phase2_store.ingest_document(payload)
        for payload in case.seed.code_sources:
            phase2_store.ingest_code(payload)

    def _collect_final_states(self, case: ReplayCase, artifact_client: TestClient) -> dict[str, str]:
        states: dict[str, str] = {}
        for task in case.seed.tasks:
            response = artifact_client.get(f"/v1/tasks/{task.task_id}")
            if response.status_code == 200:
                payload = response.json()
                states[task.task_id] = payload["state"]["state"]
        return states


def _extract_state(payload: Any) -> str | None:
    if isinstance(payload, dict):
        state = payload.get("state")
        if isinstance(state, str):
            return state
        if isinstance(state, dict):
            return state.get("state")
    return None
