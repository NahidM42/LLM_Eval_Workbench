from __future__ import annotations

from decimal import Decimal

import pytest

from llm_eval_workbench.errors import ScoreValidationError
from llm_eval_workbench.scoring import calculate_overall_score


@pytest.mark.parametrize(
    ("scores", "expected"),
    [
        ([5, 4, 4, 3, 5], Decimal("4.20")),
        ([1, 1, 1, 1, 1], Decimal("1.00")),
        ([5, 5, 5, 5, 5], Decimal("5.00")),
        ([1, 2, 3, 4, 5], Decimal("3.00")),
        ([2, 3, 3], Decimal("2.67")),
        ([2, 2, 3, 3, 3, 4, 4, 4], Decimal("3.13")),
    ],
)
def test_arithmetic_mean_and_rounding(
    scores: list[int], expected: Decimal
) -> None:
    assert calculate_overall_score(scores) == expected


def test_scoring_is_deterministic() -> None:
    scores = [5, 3, 5, 4, 5]

    assert calculate_overall_score(scores) == calculate_overall_score(scores)


def test_scoring_rejects_empty_input() -> None:
    with pytest.raises(ScoreValidationError, match="At least one"):
        calculate_overall_score([])
