from __future__ import annotations

from typing import Any

import pytest

from llm_eval_workbench.errors import InvalidEvaluationError, UnknownIssueTagError
from llm_eval_workbench.taxonomy import (
    ISSUE_DEFINITIONS,
    IssueTag,
    Severity,
    parse_issue_tag,
    parse_severity,
)
from llm_eval_workbench.validation import validate_inputs


@pytest.mark.parametrize("tag", list(IssueTag))
def test_all_documented_issue_tags_are_valid(tag: IssueTag) -> None:
    assert parse_issue_tag(tag.value) is tag
    assert ISSUE_DEFINITIONS[tag]


def test_invalid_issue_tag_is_rejected() -> None:
    with pytest.raises(UnknownIssueTagError, match="invented"):
        parse_issue_tag("invented")


@pytest.mark.parametrize("severity", list(Severity))
def test_all_severities_are_valid(severity: Severity) -> None:
    assert parse_severity(severity.value) is severity


def test_invalid_severity_is_rejected() -> None:
    with pytest.raises(InvalidEvaluationError, match="Unknown issue severity"):
        parse_severity("urgent")


def test_issue_response_excerpt_is_optional(
    task_data: dict[str, Any],
    rubric_data: dict[str, Any],
    evaluation_data: dict[str, Any],
) -> None:
    evaluation_data["issues"][0].pop("response_excerpt")

    _, _, evaluation = validate_inputs(task_data, rubric_data, evaluation_data)

    assert evaluation.issues[0].response_excerpt is None
