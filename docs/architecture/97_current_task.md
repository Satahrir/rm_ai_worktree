# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `uvm-table-schema-adapter-v1`
- Status: `MERGED`
- Role: `uvm_table_schema_adapter`
- Branch: `codex/uvm-json`
- Worktree: `rm_ref_uvm_json`
- Prompt: `agents/uvm_table_schema_adapter_agent_prompt.md`

## Goal

Implement the UVM table schema adapter that converts existing parser generic JSON into an RM schema dict accepted by SchemaDefinition.from_dict().

## Allowed Paths

- `utils/`
- `schema_defs/uvm_table/`
- `tests/test_utils/`
- `tests/fixtures/uvm_table_print/`
- `docs/interface/`

## Forbidden Paths

- `src/rm_ref/core/`
- `src/rm_ref/runtime/`
- `src/rm_ref/config/`
- `src/rm_ref/validator/`
- `src/rm_ref/packer/`
- `src/rm_ref/algorithms/`
- `src/rm_ref/io/`
- `src/rm_ref/observability/`
- `tests/test_core/`
- `tests/test_integration/`
- `tests/test_config/`
- `tests/test_validator/`
- `tests/test_packer/`
- `tests/test_algorithms/`
- `docs/architecture/`
- `agents/`
- `scripts/`
- `doc/ref_docs/`

## Required Checks

- `python -m pytest -q tests/test_utils`
- `python utils/parse_uvm_table_print.py --help`
- `python utils/uvm_table_schema_adapter.py --help`
- `python -m pytest -q`
- `D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q tests/test_utils`
- `python scripts/agent_workflow.py check-scope`

## Notes

- Formal input is uvm_table_printer-style text parsed by the existing parser; do not reimplement the text parser.
- The current fixture uses Type values such as integral[31:23] to carry bit range information.
- The target table is demo2 and scope_rules must map demo2 to cell.
- wordN rows are markers and must not become schema fields.
- Field names must include stable scope, hierarchy, word, and bit-position suffixes.
- Reserved fields remain in the schema with reserved=true.
- Payload ranges or placeholders are recorded in report or metadata, not normal SchemaDefinition fields.
- Output schema dict must be accepted by SchemaDefinition.from_dict().
- Do not implement runtime integration, run_case integration, payload_by_packet injection, full UserConfig generation, business validation rules, or Chinese description parsing.
- Keep implementation and tests Python 3.6.3-compatible.
