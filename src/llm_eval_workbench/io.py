"""UTF-8 JSON input and output helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llm_eval_workbench.errors import InputFileError


def load_json_object(path: str | Path) -> dict[str, Any]:
    """Load a UTF-8 JSON file and require an object at the top level."""

    file_path = Path(path)
    try:
        with file_path.open(encoding="utf-8") as source:
            value = json.load(source)
    except FileNotFoundError as exc:
        raise InputFileError(f"JSON file not found: {file_path}") from exc
    except json.JSONDecodeError as exc:
        raise InputFileError(
            f"Malformed JSON in {file_path} at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}."
        ) from exc
    except (OSError, UnicodeError) as exc:
        raise InputFileError(f"Could not read {file_path}: {exc}") from exc

    if not isinstance(value, dict):
        raise InputFileError(
            f"Top-level JSON value in {file_path} must be an object."
        )
    return value


def write_json_report(report: dict[str, Any], path: str | Path) -> None:
    """Write readable deterministic JSON while preserving non-ASCII text."""

    file_path = Path(path)
    try:
        serialized = json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(f"{serialized}\n", encoding="utf-8")
    except (OSError, TypeError, ValueError) as exc:
        raise InputFileError(f"Could not write JSON report to {file_path}: {exc}") from exc
