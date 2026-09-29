"""The professional default five-dimension evaluation rubric."""

from __future__ import annotations

from llm_eval_workbench.models import Criterion, Rubric, ScoreScale

DEFAULT_RUBRIC_ID = "llm-response-quality"
DEFAULT_RUBRIC_VERSION = "1.0"
DEFAULT_CRITERION_IDS = (
    "instruction_following",
    "factual_accuracy",
    "relevance",
    "completeness",
    "clarity",
)


def _criterion(
    criterion_id: str,
    name: str,
    description: str,
    anchors: tuple[str, str, str, str, str],
) -> Criterion:
    return Criterion(
        criterion_id=criterion_id,
        name=name,
        description=description,
        scoring_anchors=tuple(enumerate(anchors, start=1)),
    )


def default_rubric() -> Rubric:
    """Build the v0.1.0 default rubric without shared mutable state."""

    criteria = (
        _criterion(
            "instruction_following",
            "Instruction Following",
            "Whether the response follows explicit task instructions and constraints.",
            (
                "Major failure to follow the requested task.",
                "Several important instructions or constraints are violated.",
                "Core task is addressed, but meaningful instructions or constraints are missed.",
                "Nearly all relevant instructions are followed with only minor deviations.",
                "All relevant explicit instructions and constraints are followed correctly.",
            ),
        ),
        _criterion(
            "factual_accuracy",
            "Factual Accuracy",
            (
                "Correctness of externally verifiable claims relative to available "
                "evidence or reference material."
            ),
            (
                "Fundamental or numerous factual errors.",
                "Several important factual errors.",
                "Mostly correct but contains a meaningful error or imprecision.",
                "Correct overall with at most minor factual imprecision.",
                "No factual error is detected using the available evidence.",
            ),
        ),
        _criterion(
            "relevance",
            "Relevance",
            "Whether content directly contributes to answering the prompt.",
            (
                "Mostly irrelevant.",
                "Large portions are irrelevant.",
                "Mostly relevant but includes meaningful digression.",
                "Highly relevant with minor unnecessary content.",
                "All material is directly relevant to the task.",
            ),
        ),
        _criterion(
            "completeness",
            "Completeness",
            "Whether all important parts of the request are adequately addressed.",
            (
                "Major requested components are missing.",
                "Several important components are missing.",
                "Core request is answered but meaningful omissions remain.",
                "Nearly complete with only minor omissions.",
                "All necessary aspects are adequately addressed.",
            ),
        ),
        _criterion(
            "clarity",
            "Clarity",
            "Comprehensibility, organization, precision, and readability.",
            (
                "Very difficult to understand.",
                "Significant clarity or organization problems.",
                "Understandable but has noticeable clarity or organization weaknesses.",
                "Clear and well organized.",
                "Exceptionally clear, precise, coherent, and well organized.",
            ),
        ),
    )
    return Rubric(
        rubric_id=DEFAULT_RUBRIC_ID,
        version=DEFAULT_RUBRIC_VERSION,
        scale=ScoreScale(minimum=1, maximum=5),
        criteria=criteria,
    )
