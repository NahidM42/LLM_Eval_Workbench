from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from llm_eval_workbench.cli import build_parser, main

PROJECT_ROOT = Path(__file__).parents[1]
EXAMPLES = PROJECT_ROOT / "examples"


def _arguments(output: Path | None = None) -> list[str]:
    arguments = [
        "evaluate",
        "--task",
        str(EXAMPLES / "task.json"),
        "--rubric",
        str(EXAMPLES / "rubric.json"),
        "--evaluation",
        str(EXAMPLES / "evaluation.json"),
    ]
    if output is not None:
        arguments.extend(["--output", str(output)])
    return arguments


def _write(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False),
        encoding="utf-8",
    )


def test_root_help_command(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        build_parser().parse_args(["--help"])

    assert exc_info.value.code == 0
    assert "llm-eval" in capsys.readouterr().out


def test_evaluate_help_command(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        build_parser().parse_args(["evaluate", "--help"])

    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "--task" in output
    assert "--evaluation" in output


def test_successful_evaluation_prints_summary(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(_arguments())

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Evaluation completed." in captured.out
    assert "Overall score: 4.40 / 5" in captured.out
    assert captured.err == ""


def test_successful_evaluation_creates_output_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "report.json"

    exit_code = main(_arguments(output))

    assert exit_code == 0
    assert output.is_file()
    assert json.loads(output.read_text(encoding="utf-8"))["summary"][
        "overall_score"
    ] == 4.4
    assert str(output) in capsys.readouterr().out


def test_malformed_json_returns_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    malformed = tmp_path / "task.json"
    malformed.write_text("{", encoding="utf-8")
    arguments = _arguments()
    arguments[2] = str(malformed)

    exit_code = main(arguments)

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "Malformed JSON" in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize(
    ("input_name", "mutation", "error_code"),
    [
        ("task", lambda value: value.update(prompt=""), "invalid_task"),
        ("rubric", lambda value: value.update(criteria=[]), "invalid_rubric"),
        (
            "evaluation",
            lambda value: value["criterion_evaluations"].pop("clarity"),
            "missing_criterion",
        ),
    ],
)
def test_invalid_domain_input_returns_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    input_name: str,
    mutation: Any,
    error_code: str,
) -> None:
    paths = {
        name: EXAMPLES / f"{name}.json"
        for name in ("task", "rubric", "evaluation")
    }
    value = json.loads(paths[input_name].read_text(encoding="utf-8"))
    mutation(value)
    invalid = tmp_path / f"{input_name}.json"
    _write(invalid, value)
    paths[input_name] = invalid

    exit_code = main(
        [
            "evaluate",
            "--task",
            str(paths["task"]),
            "--rubric",
            str(paths["rubric"]),
            "--evaluation",
            str(paths["evaluation"]),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert f"Error [{error_code}]" in captured.err
    assert "Traceback" not in captured.err


def test_missing_file_returns_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    arguments = _arguments()
    arguments[2] = str(tmp_path / "missing.json")

    exit_code = main(arguments)

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "input_file_error" in captured.err
    assert "not found" in captured.err
