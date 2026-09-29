from __future__ import annotations

from typing import Any

import pytest

from llm_eval_workbench.errors import InvalidRubricError
from llm_eval_workbench.rubric import DEFAULT_CRITERION_IDS, default_rubric
from llm_eval_workbench.validation import parse_rubric


def test_valid_default_rubric_matches_example(rubric_data: dict[str, Any]) -> None:
    parsed = parse_rubric(rubric_data)

    assert parsed.to_dict() == default_rubric().to_dict()
    assert parsed.criterion_ids == DEFAULT_CRITERION_IDS


def test_rubric_rejects_empty_object() -> None:
    with pytest.raises(InvalidRubricError, match="rubric_id"):
        parse_rubric({})


def test_rubric_rejects_duplicate_criterion_ids(
    rubric_data: dict[str, Any],
) -> None:
    rubric_data["criteria"][1]["id"] = rubric_data["criteria"][0]["id"]

    with pytest.raises(InvalidRubricError, match="Duplicate"):
        parse_rubric(rubric_data)


@pytest.mark.parametrize(
    "scale",
    [
        {"min": 5, "max": 1},
        {"min": 1, "max": 1},
        {"min": 1.0, "max": 5},
        {"min": True, "max": 5},
    ],
)
def test_rubric_rejects_invalid_scoring_range(
    rubric_data: dict[str, Any], scale: object
) -> None:
    rubric_data["scale"] = scale

    with pytest.raises(InvalidRubricError, match="scale"):
        parse_rubric(rubric_data)


def test_rubric_rejects_missing_anchor(rubric_data: dict[str, Any]) -> None:
    rubric_data["criteria"][0]["scoring_anchors"].pop("3")

    with pytest.raises(InvalidRubricError, match="missing: 3"):
        parse_rubric(rubric_data)


def test_rubric_rejects_invalid_criterion(rubric_data: dict[str, Any]) -> None:
    rubric_data["criteria"][0]["description"] = ""

    with pytest.raises(InvalidRubricError, match="description"):
        parse_rubric(rubric_data)


def test_rubric_accepts_future_custom_criterion_set() -> None:
    custom = {
        "rubric_id": "custom",
        "version": "1",
        "scale": {"min": 0, "max": 2},
        "criteria": [
            {
                "id": "tone",
                "name": "Tone",
                "description": "Measures tone.",
                "scoring_anchors": {
                    "0": "Poor",
                    "1": "Acceptable",
                    "2": "Strong",
                },
            }
        ],
    }

    rubric = parse_rubric(custom)

    assert rubric.criterion_ids == ("tone",)
    assert rubric.scale.maximum == 2
