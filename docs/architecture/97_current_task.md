# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `uvm-table-parser`
- Status: `MERGED`
- Role: `uvm_table_parser`
- Branch: `codex/uvm-parser`
- Worktree: `rm_ref_uvm_parser`
- Prompt: `agents/uvm_table_parser_agent_prompt.md`

## Goal

Implement a Python 3.6-compatible hierarchical UVM table printer parser utility.

## Allowed Paths

- `utils/`
- `schema_defs/uvm_table/`
- `tests/test_utils/`
- `tests/fixtures/uvm_table_print/`
- `docs/interface/`

## Forbidden Paths

- `src/rm_ref/core/`
- `src/rm_ref/config/`
- `src/rm_ref/validator/`
- `src/rm_ref/packer/`
- `src/rm_ref/algorithms/`

## Required Checks

- `python -m pytest -q tests/test_utils`
- `python utils/parse_uvm_table_print.py --help`
- `python scripts/agent_workflow.py check-scope`

## Notes

- Create the assigned branch and worktree before implementation.
- docs/interface/uvm_table_print_parser.md is an output of the task, not a startup prerequisite.
