# LLM Eval Workbench

[![Tests](https://github.com/NahidM42/LLM_Eval_Workbench/actions/workflows/tests.yml/badge.svg)](https://github.com/NahidM42/LLM_Eval_Workbench/actions/workflows/tests.yml)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)

LLM Eval Workbench is a local Python application for structured human
evaluation of a single Large Language Model response. It validates a task, a
rubric, and an evaluator submission; calculates an equal-weight score; and
produces a stable, inspectable JSON report.

The evaluator—not this software—decides whether a response is accurate,
relevant, complete, or otherwise problematic. The workbench makes those human
judgments consistent, auditable, and machine-readable. It performs no hidden
network calls and needs no model API, paid service, API key, or external
account.

## Why structured evaluation matters

Free-form review notes are difficult to compare, validate, or reuse. A defined
rubric and controlled issue taxonomy make evaluation criteria explicit, ensure
every dimension is covered exactly once, and separate numerical quality scores
from diagnostic issue labels. This is useful in AI training, quality assurance,
research analysis, fact-checking workflows, and multilingual evaluation.

## Features

- Immutable, typed domain models for tasks, rubrics, evaluations, and issues
- Strict validation of required content, file relationships, criterion
  coverage, score bounds, rationales, issue tags, and severities
- A professional five-dimension 1–5 rubric with explicit scoring anchors
- Equal-weight arithmetic scoring with documented deterministic rounding
- UTF-8 JSON I/O that preserves Persian text with `ensure_ascii=False`
- Structured domain errors and clean non-zero CLI failures without routine
  tracebacks
- A complete Persian-language evaluation example and generated report
- 75 deterministic tests covering domain, I/O, reporting, and CLI behavior
- GitHub Actions continuous integration on Python 3.12
- Zero runtime dependencies

## Evaluation workflow

```text
Prompt + Response
        ↓
Evaluation Task + Rubric + Human Evaluation
        ↓
JSON and relationship validation
        ↓
Criterion coverage + score + taxonomy validation
        ↓
Equal-weight arithmetic mean
        ↓
Deterministic structured JSON report
```

The input is split into three files so the response under review, the scoring
policy, and the human judgment remain independently inspectable.

## Architecture

| Layer | Responsibility |
| --- | --- |
| `models.py` | Immutable domain dataclasses and JSON-safe representations |
| `validation.py` | JSON-to-domain parsing, constraints, coverage, and cross-file relationships |
| `rubric.py` | Canonical five-dimension rubric and reusable default builder |
| `taxonomy.py` | Controlled issue tags, definitions, and severity values |
| `scoring.py` | Equal-weight arithmetic mean and rounding policy |
| `report.py` | Stable schema-versioned report assembly |
| `io.py` | UTF-8 object loading and readable JSON output |
| `cli.py` | `argparse` command orchestration and user-facing errors |

The package uses a `src` layout. Validation happens at the boundary, after
which the workflow operates on frozen dataclasses. Reports intentionally omit
timestamps and host metadata so equivalent input produces equivalent output.

## Evaluation rubric

The included v1 rubric defines exactly these five default dimensions:

| Dimension | What it measures |
| --- | --- |
| `instruction_following` | Compliance with explicit instructions and constraints |
| `factual_accuracy` | Correctness relative to available evidence or reference material |
| `relevance` | Whether content directly contributes to the requested task |
| `completeness` | Whether all important requested parts are addressed |
| `clarity` | Comprehensibility, organization, precision, and readability |

A factual-accuracy score of 5 means that the evaluator detected no factual
error using the available evidence. It is not proof of absolute truth.

### Score definitions

Every criterion has criterion-specific anchors in
[`examples/rubric.json`](examples/rubric.json). Their common interpretation
is:

| Score | Interpretation |
| ---: | --- |
| 1 | Major or fundamental failure |
| 2 | Several important failures |
| 3 | Core task is addressed, but a meaningful weakness remains |
| 4 | Strong result with only minor weakness |
| 5 | Fully satisfies the criterion based on available evidence |

The overall score is the equal-weight arithmetic mean of all criterion scores.
It is calculated by the application—an input `overall_score` cannot override
it. Results are rounded to two decimal places with decimal `ROUND_HALF_UP`.
Issue severity is diagnostic and does not change the numerical score in
v0.1.0, which avoids hidden double counting.

## Issue taxonomy

| Tag | Definition |
| --- | --- |
| `factual_error` | A claim conflicts with reliable available evidence. |
| `unsupported_claim` | A claim lacks sufficient support but has not necessarily been proven false. |
| `hallucination` | Fabricated information, events, entities, details, citations, or sources are presented as real. |
| `instruction_violation` | A user instruction or constraint is not followed. |
| `irrelevant_content` | Content does not materially contribute to the requested task. |
| `omission` | Important required information is missing. |
| `reasoning_error` | The reasoning process or inference is logically defective. |
| `formatting_error` | A required output format or structural instruction is violated. |
| `citation_error` | A citation or attribution is missing, incorrect, fabricated, or does not support its claim. |

Each issue also has `minor`, `major`, or `critical` severity, a non-empty
message, and an optional response excerpt.

## Installation

Requirements:

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

```bash
git clone git@github.com:NahidM42/LLM_Eval_Workbench.git
cd LLM_Eval_Workbench
uv sync
```

`uv sync` creates the environment, installs the local package, and installs
`pytest` from the development dependency group. Runtime dependencies remain
empty.

## Usage

Show command help:

```bash
uv run llm-eval --help
uv run llm-eval evaluate --help
```

Evaluate the included example and write a report:

```bash
uv run llm-eval evaluate \
  --task examples/task.json \
  --rubric examples/rubric.json \
  --evaluation examples/evaluation.json \
  --output report.json
```

Expected summary:

```text
Evaluation completed.
Task: task-001
Overall score: 4.40 / 5
Issues: 1
Report: report.json
```

Omit `--output` to validate, score, and print the summary without writing a
report.

## Input example

The human evaluation file maps each rubric criterion to exactly one integer
score and a non-empty rationale:

```json
{
  "task_id": "task-001",
  "rubric_id": "llm-response-quality",
  "criterion_evaluations": {
    "instruction_following": {
      "score": 5,
      "rationale": "پاسخ دقیقاً در سه جمله و با زبان ساده ارائه شده است."
    }
  },
  "issues": [
    {
      "tag": "factual_error",
      "severity": "major",
      "message": "پاسخ دربارهٔ توقف کامل فرایند در تاریکی بیش از حد مطلق است."
    }
  ],
  "overall_notes": "A concise evaluator summary."
}
```

The abbreviated snippet above illustrates the shape; a valid submission must
include all five criteria. See the runnable
[`task.json`](examples/task.json),
[`rubric.json`](examples/rubric.json), and
[`evaluation.json`](examples/evaluation.json) files for complete inputs.

## Output example

The complete generated [`report.json`](examples/report.json) is committed for
inspection. Its summary is:

```json
{
  "summary": {
    "overall_score": 4.4,
    "criterion_count": 5,
    "issue_count": 1
  }
}
```

The report also contains schema version `1.0`, the task, concise rubric
metadata, all criterion scores and rationales, issues, and evaluator notes.
Large rubric anchors are not duplicated in the output.

## Errors and exit codes

- `0`: evaluation completed successfully
- `2`: invalid JSON, missing/unreadable file, validation failure, or invalid
  command arguments

Expected input problems are printed to standard error as a concise code and
message, for example:

```text
Error [missing_criterion]: Missing criterion evaluation(s): clarity.
```

## Testing

```bash
uv run pytest
```

The suite covers task and rubric validation, cross-file relationships,
criterion coverage, score boundaries and types, taxonomy controls, rounding,
deterministic reports, malformed/missing JSON, UTF-8 Persian preservation,
both help commands, output creation, and CLI failure behavior.

## Continuous integration

[`.github/workflows/tests.yml`](.github/workflows/tests.yml) runs on every
push and pull request. It checks out the repository on Ubuntu, installs
`uv` with Python 3.12, performs a locked development sync, and runs the full
pytest suite.

## Project structure

```text
LLM_Eval_Workbench/
├── .github/workflows/tests.yml
├── docs/reusable-evaluation-engine-prompt.md
├── examples/
│   ├── task.json
│   ├── rubric.json
│   ├── evaluation.json
│   └── report.json
├── src/llm_eval_workbench/
│   ├── cli.py
│   ├── errors.py
│   ├── io.py
│   ├── models.py
│   ├── report.py
│   ├── rubric.py
│   ├── scoring.py
│   ├── taxonomy.py
│   └── validation.py
├── tests/
├── pyproject.toml
└── uv.lock
```

## Design decisions

- Standard-library dataclasses, enums, JSON, `Decimal`, and `argparse` keep
  the runtime small and transparent.
- The default rubric has five fixed professional dimensions, while validation
  accepts a well-formed future rubric with a different criterion set or
  integer scale.
- Criterion evaluations are normalized into rubric order, producing stable
  reports regardless of input object key order.
- Scoring and issue diagnostics are deliberately separate.
- There are no timestamps, generated IDs, network requests, or global mutable
  rubric objects, supporting deterministic and offline execution.
- Persian is stored and emitted as real UTF-8 text, not escaped code points.

## MVP limitations

Version 0.1.0 intentionally evaluates one response with one human evaluator.
It does not implement pairwise comparison, preference ranking, multi-response
ranking, evaluator aggregation or agreement, weighted scoring, batch
analytics, databases, dashboards, model APIs, automated fact checking, or
LLM-as-a-Judge. It does not independently establish whether arbitrary claims
are true.

## Planned extensions

Possible later versions may add pairwise and preference evaluation, weighted
rubrics, agreement metrics, batch analysis, and optional LLM-as-a-Judge
experiments. These are roadmap ideas, not hidden v0.1.0 behavior.

## Portfolio relevance

This project demonstrates practical LLM evaluation design, human-in-the-loop
AI training workflows, evidence-aware fact-checking boundaries, multilingual
and Persian quality evaluation, strict data validation, deterministic report
generation, Python package design, CLI engineering, testing, and continuous
integration.

## License

No license has been selected for v0.1.0.
