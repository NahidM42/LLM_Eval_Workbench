"""Controlled issue tags and severity values for evaluator diagnostics."""

from __future__ import annotations

from enum import StrEnum

from llm_eval_workbench.errors import InvalidEvaluationError, UnknownIssueTagError


class IssueTag(StrEnum):
    FACTUAL_ERROR = "factual_error"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    HALLUCINATION = "hallucination"
    INSTRUCTION_VIOLATION = "instruction_violation"
    IRRELEVANT_CONTENT = "irrelevant_content"
    OMISSION = "omission"
    REASONING_ERROR = "reasoning_error"
    FORMATTING_ERROR = "formatting_error"
    CITATION_ERROR = "citation_error"


class Severity(StrEnum):
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


ISSUE_DEFINITIONS: dict[IssueTag, str] = {
    IssueTag.FACTUAL_ERROR: "A claim conflicts with reliable available evidence.",
    IssueTag.UNSUPPORTED_CLAIM: (
        "A claim lacks sufficient support but has not necessarily been proven false."
    ),
    IssueTag.HALLUCINATION: (
        "Fabricated information, events, entities, details, citations, or sources "
        "presented as real."
    ),
    IssueTag.INSTRUCTION_VIOLATION: (
        "A user instruction or constraint is not followed."
    ),
    IssueTag.IRRELEVANT_CONTENT: (
        "Content does not materially contribute to the requested task."
    ),
    IssueTag.OMISSION: "Important required information is missing.",
    IssueTag.REASONING_ERROR: (
        "The reasoning process or inference is logically defective."
    ),
    IssueTag.FORMATTING_ERROR: (
        "A required output format or structural instruction is violated."
    ),
    IssueTag.CITATION_ERROR: (
        "A citation or attribution is missing, incorrect, fabricated, or does not "
        "support the associated claim."
    ),
}


def parse_issue_tag(value: object) -> IssueTag:
    """Parse a taxonomy value or raise a domain-specific error."""

    if not isinstance(value, str):
        raise UnknownIssueTagError("Issue tag must be a string.")
    try:
        return IssueTag(value)
    except ValueError as exc:
        allowed = ", ".join(tag.value for tag in IssueTag)
        raise UnknownIssueTagError(
            f"Unknown issue tag '{value}'. Allowed tags: {allowed}."
        ) from exc


def parse_severity(value: object) -> Severity:
    """Parse an issue severity or raise a domain-specific error."""

    if not isinstance(value, str):
        raise InvalidEvaluationError("Issue severity must be a string.")
    try:
        return Severity(value)
    except ValueError as exc:
        allowed = ", ".join(severity.value for severity in Severity)
        raise InvalidEvaluationError(
            f"Unknown issue severity '{value}'. Allowed severities: {allowed}."
        ) from exc
