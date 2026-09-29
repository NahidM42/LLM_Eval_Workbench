"""Deterministic equal-weight arithmetic scoring."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal, ROUND_HALF_UP

from llm_eval_workbench.errors import ScoreValidationError

SCORE_PRECISION = Decimal("0.01")


def calculate_overall_score(scores: Iterable[int]) -> Decimal:
    """Return the arithmetic mean rounded to 2 decimals using ROUND_HALF_UP."""

    values = tuple(scores)
    if not values:
        raise ScoreValidationError("At least one score is required.")
    if any(not isinstance(score, int) or isinstance(score, bool) for score in values):
        raise ScoreValidationError("All scores must be integers.")
    mean = Decimal(sum(values)) / Decimal(len(values))
    return mean.quantize(SCORE_PRECISION, rounding=ROUND_HALF_UP)
