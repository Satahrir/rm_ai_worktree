# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `p3b-packet-value-codec-v1`
- Status: `READY_FOR_WORKTREE`
- Role: `packet`
- Branch: `codex/packet`
- Worktree: `rm_ref_packet`
- Prompt: `agents/packet_agent_prompt.md`

## Goal

Implement the boundary-neutral packet value model and strict identity-free in-memory packet-hex v1 codec from the approved P3A Slice 1 architecture.

## Allowed Paths

- `src/rm_ref/packet/`
- `tests/test_packet/`

## Forbidden Paths

- `src/rm_ref/core/`
- `src/rm_ref/runtime/`
- `src/rm_ref/config/`
- `src/rm_ref/schema/`
- `src/rm_ref/validator/`
- `src/rm_ref/packer/`
- `src/rm_ref/io/`
- `src/rm_ref/observability/`
- `src/rm_ref/algorithms/`
- `tests/test_core/`
- `tests/test_integration/`
- `tests/test_config/`
- `tests/test_schema/`
- `tests/test_validator/`
- `tests/test_packer/`
- `tests/test_algorithms/`
- `agents/`
- `scripts/`
- `docs/`
- `utils/`
- `schema_defs/`

## Required Checks

- `python -m pytest -q tests/test_packet`
- `python -m pytest -q`
- `$env:PYTHONPATH='src'; D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q tests/test_packet`
- `python scripts/agent_workflow.py check-scope`

## Notes

- P3A re-review closed all six findings and approved narrow Slice 1 with one nonblocking documentation wording follow-up.
- Implement only PacketWords, PacketBundle, identity-free decoded values, strict in-memory packet-hex codec, errors, serialization, and focused tests.
- Do not implement filesystem IO, manifests, binding, comparison, CASE randomization, runtime conversion, packing, numeric helpers, or layout policy.
- Keep Python 3.6.3 compatibility and do not modify core/runtime contracts.
