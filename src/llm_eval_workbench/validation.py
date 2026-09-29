"""Parsing and validation at the JSON-to-domain boundary."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from llm_eval_workbench.errors import (
    InvalidEvaluationError,
    InvalidRubricError,
    InvalidTaskError,
    MissingCriterionError,
    ScoreValidationError,
    UnknownCriterionError,
    WorkbenchError,
)
from llm_eval_workbench.models import (
    Criterion,
    CriterionEvaluation,
    EvaluationIssue,
    EvaluationSubmission,
    EvaluationTask,
    Rubric,
    ScoreScale,
)
from llm_eval_workbench.taxonomy import parse_issue_tag, parse_severity

ErrorT = TypeVar("ErrorT", bound=WorkbenchError)


def _mapping(
    value: object,
    label: str,
    error_type: type[ErrorT],
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise error_type(f"{label} must be a JSON object.")
    return value


def _non_empty_string(
    data: Mapping[str, Any],
    field: str,
    error_type: type[ErrorT],
    *,
    label: str | None = None,
) -> str:
    value = data.get(field)
    display_name = label or field
    if not isinstance(value, str) or not value.strip():
        raise error_type(f"{display_name} must be a non-empty string.")
    return value


def parse_task(data: object) -> EvaluationTask:
    """Validate task input and return an immutable domain model."""

    task = _mapping(data, "Task", InvalidTaskError)
    task_id = _non_empty_string(task, "task_id", InvalidTaskError)
    prompt = _non_empty_string(task, "prompt", InvalidTaskError)
    response = _non_empty_string(task, "response", InvalidTaskError)

    reference_answer = task.get("reference_answer")
    if reference_answer is not None and (
        not isinstance(reference_answer, str) or not reference_answer.strip()
    ):
        raise InvalidTaskError(
            "reference_answer must be null or a non-empty string."
        )

    evidence_value = task.get("evidence", [])
    if not isinstance(evidence_value, list):
        raise InvalidTaskError("evidence must be a JSON array of strings.")
    evidence: list[str] = []
    for index, entry in enumerate(evidence_value):
        if not isinstance(entry, str) or not entry.strip():
            raise InvalidTaskError(
                f"evidence[{index}] must be a non-empty string."
            )
        evidence.append(entry)

    return EvaluationTask(
        task_id=task_id,
        prompt=prompt,
        response=response,
        reference_answer=reference_answer,
        evidence=tuple(evidence),
    )


def _parse_scale(data: object) -> ScoreScale:
    scale = _mapping(data, "Rubric scale", InvalidRubricError)
    minimum = scale.get("min")
    maximum = scale.get("max")
    if (
        not isinstance(minimum, int)
        or isinstance(minimum, bool)
        or not isinstance(maximum, int)
        or isinstance(maximum, bool)
    ):
        raise InvalidRubricError("Rubric scale min and max must be integers.")
    if minimum >= maximum:
        raise InvalidRubricError(
            "Rubric scale min must be less than rubric scale max."
        )
    return ScoreScale(minimum=minimum, maximum=maximum)


def _parse_anchors(
    data: object,
    criterion_id: str,
    scale: ScoreScale,
) -> tuple[tuple[int, str], ...]:
    anchors = _mapping(
        data,
        f"Scoring anchors for criterion '{criterion_id}'",
        InvalidRubricError,
    )
    expected_scores = tuple(range(scale.minimum, scale.maximum + 1))
    expected_keys = {str(score) for score in expected_scores}
    actual_keys = set(anchors)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys, key=int)
        unexpected = sorted(actual_keys - expected_keys)
        details: list[str] = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected: {', '.join(unexpected)}")
        suffix = "; ".join(details)
        raise InvalidRubricError(
            f"Criterion '{criterion_id}' must define one anchor for every score "
            f"from {scale.minimum} to {scale.maximum} ({suffix})."
        )

    parsed: list[tuple[int, str]] = []
    for score in expected_scores:
        anchor = anchors[str(score)]
        if not isinstance(anchor, str) or not anchor.strip():
            raise InvalidRubricError(
                f"Anchor {score} for criterion '{criterion_id}' must be a "
                "non-empty string."
            )
        parsed.append((score, anchor))
    return tuple(parsed)


def parse_rubric(data: object) -> Rubric:
    """Validate a rubric while allowing future criterion sets and score ranges."""

    source = _mapping(data, "Rubric", InvalidRubricError)
    rubric_id = _non_empty_string(source, "rubric_id", InvalidRubricError)
    version = _non_empty_string(source, "version", InvalidRubricError)
    scale = _parse_scale(source.get("scale"))

    criteria_value = source.get("criteria")
    if not isinstance(criteria_value, list) or not criteria_value:
        raise InvalidRubricError("criteria must be a non-empty JSON array.")

    criteria: list[Criterion] = []
    seen_ids: set[str] = set()
    for index, raw_criterion in enumerate(criteria_value):
        criterion = _mapping(
            raw_criterion,
            f"criteria[{index}]",
            InvalidRubricError,
        )
        criterion_id = _non_empty_string(
            criterion,
            "id",
            InvalidRubricError,
            label=f"criteria[{index}].id",
        )
        if criterion_id in seen_ids:
            raise InvalidRubricError(
                f"Duplicate criterion id '{criterion_id}'."
            )
        seen_ids.add(criterion_id)
        name = _non_empty_string(
            criterion,
            "name",
            InvalidRubricError,
            label=f"Criterion '{criterion_id}' name",
        )
        description = _non_empty_string(
            criterion,
            "description",
            InvalidRubricError,
            label=f"Criterion '{criterion_id}' description",
        )
        anchors = _parse_anchors(
            criterion.get("scoring_anchors"), criterion_id, scale
        )
        criteria.append(
            Criterion(
                criterion_id=criterion_id,
                name=name,
                description=description,
                scoring_anchors=anchors,
            )
        )

    return Rubric(
        rubric_id=rubric_id,
        version=version,
        scale=scale,
        criteria=tuple(criteria),
    )


def _parse_criterion_evaluation(
    criterion_id: str,
    data: object,
    scale: ScoreScale,
) -> CriterionEvaluation:
    source = _mapping(
        data,
        f"Evaluation for criterion '{criterion_id}'",
        InvalidEvaluationError,
    )
    score = source.get("score")
    if not isinstance(score, int) or isinstance(score, bool):
        raise ScoreValidationError(
            f"Score for criterion '{criterion_id}' must be an integer."
        )
    if score < scale.minimum or score > scale.maximum:
        raise ScoreValidationError(
            f"Score for criterion '{criterion_id}' must be between "
            f"{scale.minimum} and {scale.maximum}; received {score}."
        )
    rationale = _non_empty_string(
        source,
        "rationale",
        InvalidEvaluationError,
        label=f"Rationale for criterion '{criterion_id}'",
    )
    return CriterionEvaluation(score=score, rationale=rationale)


def _parse_issue(data: object, index: int) -> EvaluationIssue:
    source = _mapping(data, f"issues[{index}]", InvalidEvaluationError)
    tag = parse_issue_tag(source.get("tag"))
    severity = parse_severity(source.get("severity"))
    message = _non_empty_string(
        source,
        "message",
        InvalidEvaluationError,
        label=f"issues[{index}].message",
    )
    excerpt = source.get("response_excerpt")
    if excerpt is not None and (
        not isinstance(excerpt, str) or not excerpt.strip()
    ):
        raise InvalidEvaluationError(
            f"issues[{index}].response_excerpt must be null or a non-empty string."
        )
    return EvaluationIssue(
        tag=tag,
        severity=severity,
        message=message,
        response_excerpt=excerpt,
    )


def parse_evaluation(
    data: object,
    task: EvaluationTask,
    rubric: Rubric,
) -> EvaluationSubmission:
    """Validate evaluator input, coverage, and task/rubric relationships."""

    source = _mapping(data, "Evaluation", InvalidEvaluationError)
    task_id = _non_empty_string(source, "task_id", InvalidEvaluationError)
    rubric_id = _non_empty_string(source, "rubric_id", InvalidEvaluationError)
    if task_id != task.task_id:
        raise InvalidEvaluationError(
            f"Evaluation task_id '{task_id}' does not match task '{task.task_id}'."
        )
    if rubric_id != rubric.rubric_id:
        raise InvalidEvaluationError(
            f"Evaluation rubric_id '{rubric_id}' does not match rubric "
            f"'{rubric.rubric_id}'."
        )

    raw_evaluations = _mapping(
        source.get("criterion_evaluations"),
        "criterion_evaluations",
        InvalidEvaluationError,
    )
    expected = set(rubric.criterion_ids)
    provided = set(raw_evaluations)
    unknown = sorted(provided - expected)
    if unknown:
        raise UnknownCriterionError(
            f"Unknown criterion evaluation(s): {', '.join(unknown)}."
        )
    missing = sorted(expected - provided)
    if missing:
        raise MissingCriterionError(
            f"Missing criterion evaluation(s): {', '.join(missing)}."
        )

    criterion_evaluations = tuple(
        (
            criterion_id,
            _parse_criterion_evaluation(
                criterion_id,
                raw_evaluations[criterion_id],
                rubric.scale,
            ),
        )
        for criterion_id in rubric.criterion_ids
    )

    raw_issues = source.get("issues")
    if not isinstance(raw_issues, list):
        raise InvalidEvaluationError("issues must be a JSON array.")
    issues = tuple(
        _parse_issue(raw_issue, index)
        for index, raw_issue in enumerate(raw_issues)
    )

    overall_notes = source.get("overall_notes")
    if not isinstance(overall_notes, str):
        raise InvalidEvaluationError("overall_notes must be a string.")

    return EvaluationSubmission(
        task_id=task_id,
        rubric_id=rubric_id,
        criterion_evaluations=criterion_evaluations,
        issues=issues,
        overall_notes=overall_notes,
    )


def validate_inputs(
    task_data: object,
    rubric_data: object,
    evaluation_data: object,
) -> tuple[EvaluationTask, Rubric, EvaluationSubmission]:
    """Validate the complete three-file workflow in dependency order."""

    task = parse_task(task_data)
    rubric = parse_rubric(rubric_data)
    evaluation = parse_evaluation(evaluation_data, task, rubric)
    return task, rubric, evaluation
