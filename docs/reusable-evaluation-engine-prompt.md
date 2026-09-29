# Reusable Module Specification: Deterministic Human Evaluation Engine

## Module name

Deterministic Human Evaluation Engine

## Purpose

Validate a structured human assessment of one text response, calculate an
equal-weight criterion score, and produce a stable JSON-safe report without
calling a model or external service.

## Problem solved

Human response reviews often arrive as inconsistent free-form notes. This
module turns a task, scoring rubric, and evaluator submission into a validated,
auditable record. It catches incomplete criterion coverage, out-of-range
scores, invalid taxonomy values, and mismatched identifiers before downstream
reporting.

## Inputs and input types

The public workflow accepts three JSON-object-compatible mappings:

1. Task
   - `task_id: str`
   - `prompt: str`
   - `response: str`
   - `reference_answer: str | None`
   - `evidence: list[str]`
2. Rubric
   - `rubric_id: str`
   - `version: str`
   - `scale: {"min": int, "max": int}`
   - `criteria: list[criterion]`
   - Each criterion has `id`, `name`, `description`, and a string-keyed
     score-to-anchor mapping.
3. Evaluation
   - `task_id: str`
   - `rubric_id: str`
   - `criterion_evaluations: dict[str, {"score": int, "rationale": str}]`
   - `issues: list[issue]`
   - `overall_notes: str`
   - Each issue has a controlled `tag`, controlled `severity`, non-empty
     `message`, and optional non-empty `response_excerpt`.

## Outputs and output types

- `validate_inputs(...) -> tuple[EvaluationTask, Rubric, EvaluationSubmission]`
- `calculate_overall_score(scores: Iterable[int]) -> Decimal`
- `build_report(...) -> dict[str, Any]`
- `load_json_object(path) -> dict[str, Any]`
- `write_json_report(report, path) -> None`
- CLI process status: `0` for success and `2` for expected input or
  operational errors.

The report contains `schema_version`, `task`, concise `rubric` metadata,
`evaluation`, and a `summary` with overall score, criterion count, and issue
count.

## Dependencies

- Python 3.12+
- Python Standard Library only at runtime
- pytest for development tests
- uv for environment, lockfile, build, and command execution

## Database dependencies

None.

## Environment variables

None.

## Security assumptions

- Input files are local UTF-8 JSON and are treated as untrusted structured
  data.
- The module does not execute input content.
- No network, subprocess, credential, secret, or API-key access occurs in the
  evaluation engine.
- Output paths are explicitly supplied by the caller. Parent directories may
  be created.
- Very large JSON resource limits are the caller's responsibility in hostile
  multi-tenant environments.

## Validation rules

- Task ID, prompt, and response are non-empty strings.
- Reference answer is null or a non-empty string.
- Evidence is an array containing only non-empty strings.
- Rubric ID and version are non-empty strings.
- Scale bounds are integers (not booleans), with `min < max`.
- Criteria are a non-empty array with unique, non-empty IDs.
- Criterion names and descriptions are non-empty.
- Every integer in the scale has exactly one non-empty scoring anchor; no
  extra anchors are accepted.
- Evaluation task and rubric IDs must match their source objects.
- Every rubric criterion has exactly one submitted evaluation.
- Unknown and missing criteria are rejected.
- Scores are integers (not booleans) inside rubric bounds.
- Rationales are non-empty strings.
- Issues use only the controlled tag and severity enums.
- Issue messages are non-empty; excerpts are null/absent or non-empty.
- Overall notes must be a string.
- Any submitted overall score is ignored; the engine calculates its own.

## Core logic

1. Decode each file as UTF-8 JSON and require a top-level object.
2. Parse and validate the task into a frozen dataclass.
3. Parse the scale and criterion definitions into a frozen rubric.
4. Verify submission identifiers against task and rubric identifiers.
5. Compare submitted criterion keys with rubric keys.
6. Validate each score and rationale in rubric order.
7. Validate issue tags, severities, messages, and excerpts.
8. Calculate `sum(scores) / count(scores)` with `Decimal`.
9. Quantize to `0.01` using `ROUND_HALF_UP`.
10. Assemble a deterministic report without timestamps or runtime metadata.
11. Serialize with two-space indentation, `ensure_ascii=False`, and
    `allow_nan=False`.

## Step-by-step operations

```python
task_data = load_json_object(task_path)
rubric_data = load_json_object(rubric_path)
evaluation_data = load_json_object(evaluation_path)
task, rubric, evaluation = validate_inputs(
    task_data, rubric_data, evaluation_data
)
report = build_report(task, rubric, evaluation)
write_json_report(report, output_path)
```

No step uses model inference. Factual judgments and issue selection must
already have been supplied by a human evaluator.

## Error handling

All expected failures derive from `WorkbenchError` and expose:

- `error_code: str`
- `message: str`
- `details: dict[str, Any]`
- `to_dict() -> {"error": ...}`

Specialized errors distinguish file failures, invalid tasks, invalid rubrics,
invalid evaluations, invalid scores, unknown criteria, missing criteria, and
unknown issue tags. The CLI writes one concise line to stderr and returns 2.
Unexpected programming errors are not silently converted into input errors.

## Edge cases

- Python booleans are rejected where integer scores or scale bounds are
  required.
- Whitespace-only strings are empty for required text checks.
- Empty issue lists are valid.
- Missing optional task fields become `None` and an empty tuple.
- Input criterion key order does not affect report order.
- A custom rubric may use a different criterion set and contiguous integer
  scale.
- A one-value scale is rejected because it cannot discriminate quality.
- Empty score sequences cannot be scored.
- Persian and other non-ASCII content survives a write/read round trip.
- Report construction excludes timestamps to remain deterministic.

## Data flow

```text
local JSON files
  -> UTF-8 object loader
  -> validation/parsing boundary
  -> immutable domain models
  -> Decimal scoring
  -> JSON-safe report dictionary
  -> optional UTF-8 report file + CLI summary
```

## API, function, and CLI contracts

```python
def validate_inputs(
    task_data: object,
    rubric_data: object,
    evaluation_data: object,
) -> tuple[EvaluationTask, Rubric, EvaluationSubmission]: ...

def calculate_overall_score(scores: Iterable[int]) -> Decimal: ...

def build_report(
    task: EvaluationTask,
    rubric: Rubric,
    evaluation: EvaluationSubmission,
) -> dict[str, Any]: ...

def load_json_object(path: str | Path) -> dict[str, Any]: ...

def write_json_report(report: dict[str, Any], path: str | Path) -> None: ...
```

CLI:

```text
llm-eval evaluate --task PATH --rubric PATH --evaluation PATH [--output PATH]
```

## Relevant files

```text
src/llm_eval_workbench/
├── errors.py
├── io.py
├── models.py
├── report.py
├── rubric.py
├── scoring.py
├── taxonomy.py
└── validation.py
```

The CLI adapter lives in `src/llm_eval_workbench/cli.py`. Examples are under
`examples/`; tests are under `tests/`.

## Tests

The module is covered by:

- `tests/test_models.py`
- `tests/test_validation.py`
- `tests/test_rubric.py`
- `tests/test_taxonomy.py`
- `tests/test_scoring.py`
- `tests/test_report.py`
- `tests/test_io.py`
- `tests/test_cli.py`

Run `uv run pytest`. Coverage includes valid workflows and every important
input boundary, deterministic scoring/reporting, UTF-8 behavior, and CLI exit
behavior.

## Acceptance criteria

- A valid three-file evaluation produces a report with schema version,
  criterion results, issues, and the correct arithmetic mean.
- Missing/unknown criteria, invalid scores, invalid taxonomy values, malformed
  JSON, and mismatched IDs fail with domain-specific errors.
- Repeated evaluation of equivalent input produces equivalent output.
- Persian content is written unescaped and read back unchanged.
- The installed CLI prints a concise summary and returns the documented status.
- The complete automated test suite passes on Python 3.12.
- No runtime package, model API, credential, database, or network is required.

## Known limitations

- One response and one evaluator per execution
- Equal-weight criteria only
- No independent factual verification
- No evaluator agreement or aggregation
- No pairwise/preference evaluation
- No batch processing, database, or web UI
- No configurable resource limits for untrusted giant JSON files

## Integration points

- File-based data pipelines can supply the three JSON mappings.
- Research annotation tools can export submissions in the documented shape.
- CI systems can treat exit code 2 as invalid evaluation data.
- A future service layer can call the pure validation, scoring, and report
  functions without invoking the CLI.
- Additional valid rubrics can be loaded without rewriting the scoring engine.

## Expected UI behavior

No graphical UI is included. Any future UI should collect the task, one score
and rationale per rubric criterion, controlled issue tags and severities, and
overall notes. It should display validation errors next to their source fields
and must not allow a user-entered overall score to override calculation.

## Expected backend behavior

The backend should validate all three objects before persisting or publishing a
report. It should preserve rubric order, calculate the score server-side, store
the report schema version, and keep issue severity separate from numeric
scoring. Expected input errors should map to client-safe structured messages;
unexpected faults should remain observable to operators.

## Example input

```json
{
  "task_id": "task-001",
  "rubric_id": "llm-response-quality",
  "criterion_evaluations": {
    "clarity": {
      "score": 5,
      "rationale": "The response is concise and easy to understand."
    }
  },
  "issues": [],
  "overall_notes": "Human evaluator notes."
}
```

This abbreviated evaluation must be expanded to cover every criterion in the
selected rubric.

## Example output

```json
{
  "schema_version": "1.0",
  "summary": {
    "overall_score": 4.4,
    "criterion_count": 5,
    "issue_count": 1
  }
}
```

## Reusable AI coding prompt

```text
Build or port a Python 3.12 module named Deterministic Human Evaluation Engine.
Its purpose is to validate and score one human evaluation of one existing text
response. Do not call an LLM, model API, paid service, database, or network.
Use only the Python Standard Library at runtime, a src package layout, frozen
slotted dataclasses, StrEnum values, explicit type hints, UTF-8 JSON, argparse,
Decimal arithmetic, uv, and pytest.

Accept three top-level JSON objects:

1. A task with non-empty task_id, prompt, response; optional non-empty
   reference_answer or null; and an evidence array of non-empty strings.
2. A rubric with non-empty rubric_id and version, integer min/max scale where
   min < max, and a non-empty criterion list. Each criterion must have a unique
   non-empty ID, name, description, and exactly one non-empty anchor for every
   integer in the score range.
3. A human evaluation with matching task_id and rubric_id, exactly one score
   and non-empty rationale for every rubric criterion, no unknown criteria, an
   issues array, and string overall_notes. Scores must be integers (booleans do
   not count) within rubric bounds.

Implement controlled issue tags factual_error, unsupported_claim,
hallucination, instruction_violation, irrelevant_content, omission,
reasoning_error, formatting_error, and citation_error. Implement minor, major,
and critical severities. Each issue needs a non-empty message and may contain a
non-empty response_excerpt. Issue severity must not modify scoring.

Calculate the equal-weight arithmetic mean. Do not accept an overall score
override. Use Decimal, round to two places with ROUND_HALF_UP, and document the
rule. Build a deterministic JSON-safe report with schema_version, task, concise
rubric metadata, evaluation, and summary containing overall_score,
criterion_count, and issue_count. Do not include timestamps or machine-specific
metadata. Normalize criterion evaluations to rubric order.

Create structured exception types for file, task, rubric, evaluation, score,
unknown criterion, missing criterion, and issue-tag errors. Each expected error
must have a stable code, readable message, JSON-safe representation, and no
routine CLI traceback. Load only UTF-8 JSON objects. Write indented UTF-8 JSON
with ensure_ascii=False and allow_nan=False.

Provide:
- a public validation function returning immutable domain models;
- a scoring function returning Decimal;
- a report builder returning a JSON-safe dict;
- JSON load/write helpers;
- an 'llm-eval evaluate' argparse command with required --task, --rubric, and
  --evaluation options plus optional --output;
- exit 0 on success and 2 for expected invalid input or file failures;
- a canonical five-criterion 1-5 rubric for instruction following, factual
  accuracy, relevance, completeness, and clarity;
- realistic UTF-8 sample inputs and a generated sample report;
- comprehensive pytest tests for valid and invalid boundary behavior;
- a simple GitHub Actions workflow using uv and Python 3.12;
- documentation of architecture, contracts, scoring, taxonomy, security
  assumptions, limitations, and runnable commands.

Keep validation independent of the canonical criterion set so future
well-formed rubrics can be supplied. Keep the scoring engine unweighted. Avoid
Pydantic, pandas, web frameworks, plugin systems, async architecture, and
premature abstractions. Verify uv sync, the complete tests, package import, both
help commands, and the real example CLI workflow before completion.
```
