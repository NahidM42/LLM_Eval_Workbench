"""Stable JSON-safe report assembly."""

from __future__ import annotations

from typing import Any

from llm_eval_workbench.models import EvaluationSubmission, EvaluationTask, Rubric
from llm_eval_workbench.scoring import calculate_overall_score

SCHEMA_VERSION = "1.0"


def build_report(
    task: EvaluationTask,
    rubric: Rubric,
    evaluation: EvaluationSubmission,
) -> dict[str, Any]:
    """Build a deterministic report without timestamps or environment metadata."""

    overall_score = calculate_overall_score(evaluation.scores)
    rubric_metadata = {
        "rubric_id": rubric.rubric_id,
        "version": rubric.version,
        "scale": rubric.scale.to_dict(),
        "criteria": [
            {"id": criterion.criterion_id, "name": criterion.name}
            for criterion in rubric.criteria
        ],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "task": task.to_dict(),
        "rubric": rubric_metadata,
        "evaluation": evaluation.to_dict(),
        "summary": {
            "overall_score": float(overall_score),
            "criterion_count": len(evaluation.criterion_evaluations),
            "issue_count": len(evaluation.issues),
        },
    }
