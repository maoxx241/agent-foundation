from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

from libs.schemas import ArtifactStage, TaskState
from libs.storage.fs_utils import ConflictError
from libs.storage.state_machine import NEXT_STATE, ROLLBACKS, validate_transition


def _seed_full_task_tree(task_root: Path) -> None:
    for stage in ArtifactStage:
        (task_root / stage.value).mkdir(parents=True, exist_ok=True)

    (task_root / "00_task" / "task-brief.json").write_text("{}", encoding="utf-8")
    (task_root / "10_evidence" / "evidence-pack.json").write_text("{}", encoding="utf-8")
    (task_root / "20_design" / "design-spec.json").write_text("{}", encoding="utf-8")
    (task_root / "20_design" / "design-review.json").write_text(
        json.dumps({"verdict": "approve", "required_changes": []}),
        encoding="utf-8",
    )
    (task_root / "30_test" / "test-spec.json").write_text("{}", encoding="utf-8")
    (task_root / "30_test" / "acceptance.json").write_text("{}", encoding="utf-8")
    (task_root / "40_dev" / "patch.diff").write_text("diff", encoding="utf-8")
    (task_root / "40_dev" / "changed-files.json").write_text("[]", encoding="utf-8")
    (task_root / "40_dev" / "selftest.json").write_text("{}", encoding="utf-8")
    (task_root / "50_review" / "impl-review.json").write_text(
        json.dumps({"verdict": "approve", "required_fixes": []}),
        encoding="utf-8",
    )
    (task_root / "60_validation" / "validation-report.json").write_text(
        json.dumps({"passed": True}),
        encoding="utf-8",
    )
    (task_root / "60_validation" / "regression.json").write_text("{}", encoding="utf-8")
    (task_root / "70_release" / "adr.json").write_text("{}", encoding="utf-8")
    (task_root / "70_release" / "changelog.md").write_text("# Changelog", encoding="utf-8")
    (task_root / "80_writeback" / "experience-packet.json").write_text("{}", encoding="utf-8")
    (task_root / "80_writeback" / "finalization.json").write_text("{}", encoding="utf-8")


@given(
    current=st.sampled_from(list(TaskState)),
    target=st.sampled_from(list(TaskState)),
)
def test_state_machine_only_allows_next_or_documented_rollbacks(current: TaskState, target: TaskState):
    with tempfile.TemporaryDirectory() as temp_dir:
        task_root = Path(temp_dir) / "task"
        _seed_full_task_tree(task_root)

        allowed = NEXT_STATE.get(current) == target or target in ROLLBACKS.get(current, set())
        if current == target or not allowed:
            with pytest.raises(ConflictError):
                validate_transition(task_root, current, target)
        else:
            validate_transition(task_root, current, target)
