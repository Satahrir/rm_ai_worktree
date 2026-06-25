# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `uvm-table-config-adapter-v1`
- Status: `MERGED`
- Role: `uvm_table_config_adapter`
- Branch: `codex/uvm-config`
- Worktree: `rm_ref_uvm_config`
- Prompt: `agents/uvm_table_config_adapter_agent_prompt.md`

## Goal

Implement the minimal UVM table value-binding adapter that converts parser generic JSON values plus SchemaDefinition into an RM UserConfig-compatible dict and verifies the resolver-to-CellConfig path without runtime execution.

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
- `python utils/uvm_table_config_adapter.py --help`
- `python -m pytest -q`
- `D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q tests/test_utils`
- `python scripts/agent_workflow.py check-scope`

## Notes

- Formal input is uvm_table_printer-style text parsed by the existing parser; do not reimplement the text parser.
- This task binds parser leaf values to an injected SchemaDefinition and emits a UserConfig-compatible dict.
- Field matching must not rely only on raw names when duplicates exist; use scope/word/bit/raw-name matching before unique raw-name fallback.
- First version supports packet and cell scopes, defaulting to packet_index=0 and cell_index=0 only for a single unambiguous context.
- Reserved fields and payload placeholders must not enter normal UserConfig values.
- Smoke verification should cover UserConfig.from_dict(), ConfigResolver.resolve(), and ResolvedConfig.to_core_config() reaching CellConfig.parameters.
- Do not implement runtime integration, run_case integration, payload_by_packet injection, algorithm execution, validator business rule generation, or Chinese description parsing.
- Keep implementation and tests Python 3.6.3-compatible.
