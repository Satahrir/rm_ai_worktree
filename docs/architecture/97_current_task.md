# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `uvm-table-json`
- Status: `READY`
- Role: `uvm_table_json`
- Branch: `codex/uvm-json`
- Worktree: `rm_ref_uvm_json`
- Prompt: `agents/uvm_table_json_agent_prompt.md`

## Goal

Add deterministic hierarchical JSON output to the existing UVM table-printer parser.

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

- Implement generic hierarchical JSON before RM-specific mapping or adaptation.
- Keep the existing Python output as the default and preserve backward compatibility.
- Do not reuse the completed rm_ref_uvm_parser worktree.
