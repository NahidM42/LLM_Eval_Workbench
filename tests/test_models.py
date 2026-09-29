from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from llm_eval_workbench.models import EvaluationTask
from llm_eval_workbench.validation import parse_task


def test_task_model_is_immutable(task_data: dict[str, object]) -> None:
    task = parse_task(task_data)

    with pytest.raises(FrozenInstanceError):
        task.task_id = "changed"  # type: ignore[misc]


def test_task_to_dict_is_json_safe(task_data: dict[str, object]) -> None:
    task = parse_task(task_data)

    serialized = task.to_dict()

    assert isinstance(serialized["evidence"], list)
    assert serialized["reference_answer"] == task_data["reference_answer"]


def test_task_optional_fields_use_safe_defaults() -> None:
    task = parse_task(
        {"task_id": "task", "prompt": "Prompt", "response": "Response"}
    )

    assert task == EvaluationTask("task", "Prompt", "Response")
    assert task.reference_answer is None
    assert task.evidence == ()
