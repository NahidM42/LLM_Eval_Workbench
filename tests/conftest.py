from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).parents[1]
EXAMPLES = PROJECT_ROOT / "examples"


def _read_example(name: str) -> dict[str, Any]:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


@pytest.fixture
def task_data() -> dict[str, Any]:
    return copy.deepcopy(_read_example("task.json"))


@pytest.fixture
def rubric_data() -> dict[str, Any]:
    return copy.deepcopy(_read_example("rubric.json"))


@pytest.fixture
def evaluation_data() -> dict[str, Any]:
    return copy.deepcopy(_read_example("evaluation.json"))
