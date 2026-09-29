"""Command-line interface for the single-response evaluation workflow."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from llm_eval_workbench.errors import WorkbenchError
from llm_eval_workbench.io import load_json_object, write_json_report
from llm_eval_workbench.report import build_report
from llm_eval_workbench.validation import validate_inputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llm-eval",
        description="Validate and score a human evaluation of one LLM response.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    evaluate = subparsers.add_parser(
        "evaluate",
        help="evaluate one response from task, rubric, and evaluation JSON files",
    )
    evaluate.add_argument("--task", required=True, help="path to task JSON")
    evaluate.add_argument("--rubric", required=True, help="path to rubric JSON")
    evaluate.add_argument(
        "--evaluation", required=True, help="path to human evaluation JSON"
    )
    evaluate.add_argument(
        "--output",
        help="optional path for the structured JSON report",
    )
    return parser


def _run_evaluate(args: argparse.Namespace) -> int:
    task_data = load_json_object(args.task)
    rubric_data = load_json_object(args.rubric)
    evaluation_data = load_json_object(args.evaluation)
    task, rubric, evaluation = validate_inputs(
        task_data, rubric_data, evaluation_data
    )
    report = build_report(task, rubric, evaluation)
    if args.output:
        write_json_report(report, args.output)

    print("Evaluation completed.")
    print(f"Task: {task.task_id}")
    print(
        f"Overall score: {report['summary']['overall_score']:.2f} "
        f"/ {rubric.scale.maximum}"
    )
    print(f"Issues: {report['summary']['issue_count']}")
    if args.output:
        print(f"Report: {args.output}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "evaluate":
            return _run_evaluate(args)
    except WorkbenchError as exc:
        print(f"Error [{exc.error_code}]: {exc.message}", file=sys.stderr)
        return 2
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
