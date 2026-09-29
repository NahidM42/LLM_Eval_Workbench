from __future__ import annotations

import json
from typing import Any

from llm_eval_workbench.report import SCHEMA_VERSION, build_report
from llm_eval_workbench.validation import validate_inputs


def test_report_has_expected_schema_and_summary(
    task_data: dict[str, Any],
    rubric_data: dict[str, Any],
    evaluation_data: dict[str, Any],
) -> None:
    task, rubric, evaluation = validate_inputs(
        task_data, rubric_data, evaluation_data
    )

    report = build_report(task, rubric, evaluation)

    assert report["schema_version"] == SCHEMA_VERSION
    assert report["summary"] == {
        "overall_score": 4.4,
        "criterion_count": 5,
        "issue_count": 1,
    }


def test_report_contains_scores_rationales_and_issues(
    task_data: dict[str, Any],
    rubric_data: dict[str, Any],
    evaluation_data: dict[str, Any],
) -> None:
    models = validate_inputs(task_data, rubric_data, evaluation_data)

    report = build_report(*models)

    assert (
        report["evaluation"]["criterion_evaluations"]["factual_accuracy"]["score"]
        == 3
    )
    assert report["evaluation"]["issues"][0]["tag"] == "factual_error"
    assert report["task"]["reference_answer"] == task_data["reference_answer"]


def test_report_is_json_safe_and_deterministic(
    task_data: dict[str, Any],
    rubric_data: dict[str, Any],
    evaluation_data: dict[str, Any],
) -> None:
    models = validate_inputs(task_data, rubric_data, evaluation_data)

    first = build_report(*models)
    second = build_report(*models)

    assert first == second
    assert json.dumps(first, ensure_ascii=False, sort_keys=True) == json.dumps(
        second, ensure_ascii=False, sort_keys=True
    )
    assert "دانش‌آموز" in json.dumps(first, ensure_ascii=False)
