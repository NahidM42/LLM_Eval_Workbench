"""Immutable domain models used by the evaluation workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from llm_eval_workbench.taxonomy import IssueTag, Severity


@dataclass(frozen=True, slots=True)
class EvaluationTask:
    task_id: str
    prompt: str
    response: str
    reference_answer: str | None = None
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "prompt": self.prompt,
            "response": self.response,
            "reference_answer": self.reference_answer,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class ScoreScale:
    minimum: int
    maximum: int

    def to_dict(self) -> dict[str, int]:
        return {"min": self.minimum, "max": self.maximum}


@dataclass(frozen=True, slots=True)
class Criterion:
    criterion_id: str
    name: str
    description: str
    scoring_anchors: tuple[tuple[int, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.criterion_id,
            "name": self.name,
            "description": self.description,
            "scoring_anchors": {
                str(score): anchor for score, anchor in self.scoring_anchors
            },
        }


@dataclass(frozen=True, slots=True)
class Rubric:
    rubric_id: str
    version: str
    scale: ScoreScale
    criteria: tuple[Criterion, ...]

    @property
    def criterion_ids(self) -> tuple[str, ...]:
        return tuple(criterion.criterion_id for criterion in self.criteria)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rubric_id": self.rubric_id,
            "version": self.version,
            "scale": self.scale.to_dict(),
            "criteria": [criterion.to_dict() for criterion in self.criteria],
        }


@dataclass(frozen=True, slots=True)
class CriterionEvaluation:
    score: int
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {"score": self.score, "rationale": self.rationale}


@dataclass(frozen=True, slots=True)
class EvaluationIssue:
    tag: IssueTag
    severity: Severity
    message: str
    response_excerpt: str | None = None

    def to_dict(self) -> dict[str, Any]:
        issue: dict[str, Any] = {
            "tag": self.tag.value,
            "severity": self.severity.value,
            "message": self.message,
        }
        if self.response_excerpt is not None:
            issue["response_excerpt"] = self.response_excerpt
        return issue


@dataclass(frozen=True, slots=True)
class EvaluationSubmission:
    task_id: str
    rubric_id: str
    criterion_evaluations: tuple[tuple[str, CriterionEvaluation], ...]
    issues: tuple[EvaluationIssue, ...]
    overall_notes: str

    @property
    def scores(self) -> tuple[int, ...]:
        return tuple(result.score for _, result in self.criterion_evaluations)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "rubric_id": self.rubric_id,
            "criterion_evaluations": {
                criterion_id: result.to_dict()
                for criterion_id, result in self.criterion_evaluations
            },
            "issues": [issue.to_dict() for issue in self.issues],
            "overall_notes": self.overall_notes,
        }
