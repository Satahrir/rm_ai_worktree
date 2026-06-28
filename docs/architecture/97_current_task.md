# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `p2b-uvm-table-runtime-boundary`
- Status: `REVIEW`
- Role: `runtime`
- Branch: `main`
- Worktree: `rm_ref_main`
- Prompt: `agents/runtime_agent_prompt.md`

## Goal

Implement the formal UVM table runtime boundary from uvm_table_printer text or parser JSON into run_case(), preserving OrchestrationResult and core boundaries.

## Allowed Paths

- `tests/test_integration/`
- `src/rm_ref/io/`
- `src/rm_ref/runtime/`
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
- Add formal run_uvm_table_text_case() and run_uvm_table_json_case() boundary APIs.
- Preserve run_case() OrchestrationResult without redesigning runtime status semantics.
- Assert reserved fields and payload placeholders are not visible as normal parameters.
- Pass payload_by_packet=None only; payload injection remains future work.
- Do not integrate a UVM simulator, real business algorithm, broad CLI workflow, or new status model.
- Keep implementation and tests Python 3.6.3-compatible.
