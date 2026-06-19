# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `runtime-orchestration-v1`
- Status: `READY`
- Role: `runtime`
- Branch: `codex/runtime`
- Worktree: `rm_ref_runtime`
- Prompt: `agents/runtime_agent_prompt.md`

## Goal

Implement the P1 runtime orchestration boundary with OrchestrationResult, validation gating, payload injection, and cross-layer integration tests.

## Allowed Paths

- `src/rm_ref/runtime/`
- `tests/test_integration/`
- `src/rm_ref/__init__.py`

## Forbidden Paths

- `src/rm_ref/core/`
- `src/rm_ref/schema/`
- `src/rm_ref/config/`
- `src/rm_ref/validator/`
- `src/rm_ref/packer/`
- `src/rm_ref/algorithms/`
- `src/rm_ref/io/`
- `src/rm_ref/observability/`
- `tests/test_core/`
- `tests/test_schema/`
- `tests/test_config/`
- `tests/test_validator/`
- `tests/test_packer/`
- `tests/test_algorithms/`
- `tests/test_utils/`
- `utils/`
- `schema_defs/`
- `docs/`
- `scripts/`
- `agents/`

## Required Checks

- `python -m pytest -q tests/test_integration`
- `python -m pytest -q tests/test_config`
- `python -m pytest -q tests/test_validator`
- `python -m pytest -q tests/test_core`
- `python -m pytest -q`
- `D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q`
- `python scripts/agent_workflow.py check-scope`

## Notes

- Follow the decided P1 runtime contracts in docs/architecture/13_current_implemented_flow.md and docs/architecture/14_p1_design_questions.md.
- Add rm_ref.runtime as the outer composition layer; do not move this logic into rm_ref.core.
- Provide run_case(user_config, schema, algorithm, payload_by_packet=None).
- Runtime receives an explicit SchemaDefinition and an already constructed Algorithm instance.
- Core execution must not run when ValidationResult.ok is false.
- OrchestrationResult statuses are PASS, SETUP_ERROR, VALIDATION_ERROR, and EXECUTION_ERROR.
- Only ConfigResolutionError and PayloadMappingError are converted to SETUP_ERROR.
- Payload mapping is payload_by_packet[packet_index][cell_index]; missing entries map to [].
- Extra packet/cell payload indexes and malformed mappings produce PayloadMappingError and SETUP_ERROR.
- Payload values are opaque and deep-copied into core config.
- Do not implement algorithm selection, schema registries, payload file IO, result directories, CLI policy, or packer integration.
- Keep all code and tests Python 3.6.3-compatible.
