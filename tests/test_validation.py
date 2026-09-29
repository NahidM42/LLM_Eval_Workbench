from __future__ import annotations

from typing import Any

import pytest

from llm_eval_workbench.errors import (
    InvalidEvaluationError,
    InvalidTaskError,
    MissingCriterionError,
    ScoreValidationError,
    UnknownCriterionError,
)
from llm_eval_workbench.validation import (
    parse_evaluation,
    parse_rubric,
    parse_task,
    validate_inputs,
)


def test_valid_task_with_reference_and_evidence(task_data: dict[str, Any]) -> None:
    task = parse_task(task_data)

    assert task.task_id == "task-001"
    assert task.reference_answer
    assert len(task.evidence) == 2


@pytest.mark.parametrize("field", ["task_id", "prompt", "response"])
def test_task_rejects_empty_required_text(
    task_data: dict[str, Any], field: str
) -> None:
    task_data[field] = "  "

    with pytest.raises(InvalidTaskError, match=field):
        parse_task(task_data)


@pytest.mark.parametrize("evidence", [["valid", ""], ["valid", 4], "not-a-list"])
def test_task_rejects_invalid_evidence(
    task_data: dict[str, Any], evidence: object
) -> None:
    task_data["evidence"] = evidence

    with pytest.raises(InvalidTaskError, match="evidence"):
        parse_task(task_data)


def test_complete_evaluation_is_ordered_by_rubric(
    task_data: dict[str, Any],
    rubric_data: dict[str, Any],
    evaluation_data: dict[str, Any],
) -> None:
    task, rubric, evaluation = validate_inputs(
        task_data, rubric_data, evaluation_data
    )

    assert evaluation.task_id == task.task_id
    assert tuple(key for key, _ in evaluation.criterion_evaluations) == (
        rubric.criterion_ids
    )


def test_evaluation_rejects_missing_criterion(
    task_data: dict[str, Any],
    rubric_data: dict[str, Any],
    evaluation_data: dict[str, Any],
) -> None:
    evaluation_data["criterion_evaluations"].pop("clarity")

    with pytest.raises(MissingCriterionError, match="clarity"):
        validate_inputs(task_data, rubric_data, evaluation_data)


def test_evaluation_rejects_unknown_criterion(
    task_data: dict[str, Any],
    rubric_data: dict[str, Any],
    evaluation_data: dict[str, Any],
) -> None:
    evaluation_data["criterion_evaluations"]["style"] = {
        "score": 4,
        "rationale": "Clear style.",
    }

    with pytest.raises(UnknownCriterionError, match="style"):
        validate_inputs(task_data, rubric_data, evaluation_data)


@pytest.mark.parametrize("score", [0, 6])
def test_evaluation_rejects_out_of_range_score(
    task_data: dict[str, Any],
    rubric_data: dict[str, Any],
    evaluation_data: dict[str, Any],
    score: int,
) -> None:
    evaluation_data["criterion_evaluations"]["clarity"]["score"] = score

    with pytest.raises(ScoreValidationError, match="between 1 and 5"):
        validate_inputs(task_data, rubric_data, evaluation_data)


@pytest.mark.parametrize("score", [3.5, "4", True])
def test_evaluation_rejects_non_integer_score(
    task_data: dict[str, Any],
    rubric_data: dict[str, Any],
    evaluation_data: dict[str, Any],
    score: object,
) -> None:
    evaluation_data["criterion_evaluations"]["clarity"]["score"] = score

    with pytest.raises(ScoreValidationError, match="integer"):
        validate_inputs(task_data, rubric_data, evaluation_data)


def test_evaluation_rejects_empty_rationale(
    task_data: dict[str, Any],
    rubric_data: dict[str, Any],
    evaluation_data: dict[str, Any],
) -> None:
    evaluation_data["criterion_evaluations"]["clarity"]["rationale"] = ""

    with pytest.raises(InvalidEvaluationError, match="Rationale"):
        validate_inputs(task_data, rubric_data, evaluation_data)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("task_id", "other-task", "does not match task"),
        ("rubric_id", "other-rubric", "does not match rubric"),
    ],
)
def test_evaluation_rejects_relationship_mismatch(
    task_data: dict[str, Any],
    rubric_data: dict[str, Any],
    evaluation_data: dict[str, Any],
    field: str,
    value: str,
    expected: str,
) -> None:
    evaluation_data[field] = value
    task = parse_task(task_data)
    rubric = parse_rubric(rubric_data)

    with pytest.raises(InvalidEvaluationError, match=expected):
        parse_evaluation(evaluation_data, task, rubric)
