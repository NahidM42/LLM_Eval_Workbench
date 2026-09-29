from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm_eval_workbench.errors import InputFileError
from llm_eval_workbench.io import load_json_object, write_json_report


def test_load_valid_json_object(tmp_path: Path) -> None:
    path = tmp_path / "valid.json"
    path.write_text('{"name": "ارزیابی"}', encoding="utf-8")

    assert load_json_object(path) == {"name": "ارزیابی"}


def test_load_missing_file(tmp_path: Path) -> None:
    with pytest.raises(InputFileError, match="not found"):
        load_json_object(tmp_path / "missing.json")


def test_load_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"broken":', encoding="utf-8")

    with pytest.raises(InputFileError, match="Malformed JSON"):
        load_json_object(path)


@pytest.mark.parametrize("value", [["item"], "text", 4, None])
def test_load_rejects_wrong_top_level_type(tmp_path: Path, value: object) -> None:
    path = tmp_path / "value.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(InputFileError, match="Top-level JSON"):
        load_json_object(path)


def test_write_json_preserves_persian_and_indentation(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "report.json"

    write_json_report({"message": "پاسخ روشن است", "score": 4.4}, path)

    text = path.read_text(encoding="utf-8")
    assert "پاسخ روشن است" in text
    assert "\\u" not in text
    assert text.startswith("{\n  ")
    assert text.endswith("\n")
    assert load_json_object(path)["score"] == 4.4


def test_write_rejects_non_json_safe_value(tmp_path: Path) -> None:
    with pytest.raises(InputFileError, match="Could not write"):
        write_json_report({"invalid": object()}, tmp_path / "report.json")
