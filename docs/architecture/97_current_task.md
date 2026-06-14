# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `validation-result-serialization-v1`
- Status: `REVIEW`
- Role: `config`
- Branch: `codex/config`
- Worktree: `rm_ref_config`
- Prompt: `agents/config_agent_prompt.md`

## Goal

Implement stable plain-data serialization for ValidationIssue and ValidationResult.

## Allowed Paths

- `src/rm_ref/validator/`
- `tests/test_validator/`

## Forbidden Paths

- `src/rm_ref/core/`
- `src/rm_ref/schema/`
- `src/rm_ref/config/`
- `src/rm_ref/packer/`
- `src/rm_ref/algorithms/`
- `src/rm_ref/io/`
- `src/rm_ref/observability/`
- `tests/test_core/`
- `tests/test_schema/`
- `tests/test_config/`
- `utils/`
- `schema_defs/`
- `docs/`
- `scripts/`
- `agents/`

## Required Checks

- `python -m pytest -q tests/test_validator`
- `python -m pytest -q tests/test_config`
- `python -m pytest -q tests/test_schema`
- `python -m pytest -q`
- `D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q`
- `python scripts/agent_workflow.py check-scope`

## Notes

- Follow the decided Question 6 contract in docs/architecture/14_p1_design_questions.md.
- ValidationIssue.to_dict() emits every fixed field, including None values.
- ValidationResult.to_dict() emits ok, errors, and warnings while preserving discovery order.
- Plain-value conversion supports scalar values, dicts with scalar keys, lists, tuples, sets, and frozensets.
- Unsupported values and keys raise TypeError; do not stringify them.
- Serialized output must not share mutable containers with issue values.
- Do not import serialization helpers from rm_ref.core.
- Do not change ValidationIssue constructor ownership behavior.
- Feature implementation committed as e790162 on codex/config.
- Focused validator tests passed: 16.
- Config and schema regression tests passed: 17.
- Modern Python full regression tests passed: 141.
- Python 3.6.3 full regression tests passed: 141 with the known pytest.ini pythonpath warning.
- Scope check and git diff check passed.
