# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `p2b-uvm-table-runtime-boundary-review`
- Status: `READY`
- Role: `review`
- Branch: `codex/review`
- Worktree: `rm_ref_review`
- Prompt: `agents/p2b_uvm_table_runtime_review_prompt.md`

## Goal

Independently review the formal UVM table runtime boundary from uvm_table_printer text or parser JSON into run_case(), and record a merge recommendation.

## Allowed Paths

- `docs/review/`

## Forbidden Paths

- `src/`
- `tests/`
- `utils/`
- `schema_defs/`
- `agents/`
- `scripts/`
- `docs/architecture/`

## Required Checks

- `python -m pytest -q tests/test_integration/system_cases/uvm_table_printer_to_algorithm`
- `python -m pytest -q tests/test_utils`
- `python -m pytest -q`
- `$env:PYTHONPATH='src'; D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q tests/test_integration/system_cases/uvm_table_printer_to_algorithm`
- `python scripts/agent_workflow.py check-scope`

## Notes

- Review commit 33306bc against its parent and the active UVM table boundary contracts.
- Write only docs/review/p2b_uvm_table_runtime_boundary_review.md.
- Do not modify production code, tests, workflow status, adapters, or generated artifacts.
- The known Python 3.6 pytest import-path issue is a follow-up candidate; assess it without fixing it.
