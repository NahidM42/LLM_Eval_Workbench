"""Structured exceptions raised by the evaluation workbench."""

from __future__ import annotations

from typing import Any, ClassVar, Mapping


class WorkbenchError(Exception):
    """Base class for expected, user-correctable workbench errors."""

    error_code: ClassVar[str] = "workbench_error"

    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        """Return a stable JSON-safe representation of the error."""

        error: dict[str, Any] = {
            "code": self.error_code,
            "message": self.message,
        }
        if self.details:
            error["details"] = self.details
        return {"error": error}


class InputFileError(WorkbenchError):
    """An input or output JSON file cannot be processed."""

    error_code = "input_file_error"


class InvalidTaskError(WorkbenchError):
    """The evaluation task is malformed."""

    error_code = "invalid_task"


class InvalidRubricError(WorkbenchError):
    """The rubric is malformed."""

    error_code = "invalid_rubric"


class InvalidEvaluationError(WorkbenchError):
    """The human evaluation submission is malformed."""

    error_code = "invalid_evaluation"


class ScoreValidationError(InvalidEvaluationError):
    """A submitted score is not a valid integer within the rubric scale."""

    error_code = "invalid_score"


class UnknownCriterionError(InvalidEvaluationError):
    """A submission evaluates a criterion that the rubric does not define."""

    error_code = "unknown_criterion"


class MissingCriterionError(InvalidEvaluationError):
    """A submission does not evaluate every rubric criterion."""

    error_code = "missing_criterion"


class UnknownIssueTagError(InvalidEvaluationError):
    """An issue uses a tag outside the controlled taxonomy."""

    error_code = "unknown_issue_tag"
