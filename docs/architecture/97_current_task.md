# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `p4a-runtime-data-ownership-core-contract-hardening`
- Status: `READY`
- Role: `phase1-refactor`
- Branch: `codex/phase1-runtime-contracts`
- Worktree: `rm_ref_phase1`
- Prompt: `agents/phase1_refactor_agent_prompt.md`

## Goal

Perform a behavior-preserving Phase 1 refactor of payload ownership, static config construction, and the CellContext public contract.

## Allowed Paths

- `src/rm_ref/core/`
- `src/rm_ref/config/`
- `src/rm_ref/runtime/`
- `tests/test_core/`
- `tests/test_config/`
- `tests/test_integration/`

## Forbidden Paths

- `src/rm_ref/schema/`
- `src/rm_ref/validator/`
- `src/rm_ref/packer/`
- `src/rm_ref/packet/`
- `src/rm_ref/observability/`
- `src/rm_ref/algorithms/`
- `tests/test_schema/`
- `tests/test_validator/`
- `tests/test_packer/`
- `tests/test_packet/`
- `tests/test_algorithms/`
- `agents/`
- `scripts/`
- `docs/`
- `utils/`
- `schema_defs/`

## Required Checks

- `python -m pytest -q tests/test_core tests/test_config tests/test_integration`
- `python -m pytest -q`
- `$env:PYTHONPATH='src'; D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q tests/test_core tests/test_config tests/test_integration`
- `$env:PYTHONPATH='src'; D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q`
- `python scripts/agent_workflow.py check-scope`

## Notes

- The full-test baseline on main is 197 passed under the default Python environment.
- This is a behavior-preserving refactor; keep the existing vertical flow and public contracts stable.
- Priority is payload ownership, then static config mutation, then the CellContext public API.
- Task p3b-packet-value-codec-v1 is retained as an approved lower-priority follow-up and must not be implemented in this task.
- Keep Python 3.6.3 compatibility and add no third-party runtime dependencies.
