# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `p2b-uvm-table-run-case-smoke`
- Status: `READY`
- Role: `runtime`
- Branch: `codex/runtime`
- Worktree: `rm_ref_runtime`
- Prompt: `agents/runtime_agent_prompt.md`

## Goal

Implement a minimal runtime integration smoke proving UVM table config adapter output can enter run_case(), drive a small Algorithm, and expose packet/cell parameters without payload injection or simulator integration.

## Allowed Paths

- `tests/test_integration/`
- `docs/architecture/`
- `tests/fixtures/uvm_table_print/`
- `agents/`
- `utils/`
- `schema_defs/uvm_table/`

## Forbidden Paths

- `src/rm_ref/core/`
- `src/rm_ref/config/`
- `src/rm_ref/validator/`
- `src/rm_ref/packer/`
- `src/rm_ref/algorithms/`
- `src/rm_ref/io/`
- `src/rm_ref/observability/`
- `tests/test_core/`
- `tests/test_config/`
- `tests/test_validator/`
- `tests/test_packer/`
- `tests/test_algorithms/`
- `scripts/`
- `doc/ref_docs/`

## Required Checks

- `python -m pytest -q tests/test_utils`
- `python -m pytest -q tests/test_integration/test_uvm_table_run_case_smoke.py`
- `python -m pytest -q`
- `D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q tests/test_integration/test_uvm_table_run_case_smoke.py`
- `python scripts/agent_workflow.py validate`
- `python scripts/agent_workflow.py check-scope`

## Notes

- P2A is complete and merged; do not refactor the UVM parser/schema/config adapters.
- Use existing run_case(user_config, schema, algorithm, payload_by_packet=None).
- Add the minimal integration smoke proving adapter-generated UserConfig drives Algorithm execution.
- The smoke Algorithm may be test-local and should read packet and cell configuration visible at execution time.
- Assert reserved fields and payload placeholders are not visible as normal parameters.
- Pass payload_by_packet=None only; payload injection remains future work.
- Do not integrate a UVM simulator, real business algorithm, broad CLI workflow, or new status model.
- Keep implementation and tests Python 3.6.3-compatible.
