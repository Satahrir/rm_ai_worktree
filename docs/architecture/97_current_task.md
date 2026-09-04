# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `p1a1-payload-working-copy-ownership`
- Status: `READY`
- Role: `phase1-refactor`
- Branch: `codex/p1a-payload-ownership`
- Worktree: `rm_ref_p1a`
- Prompt: `agents/p1a1_payload_ownership_agent_prompt.md`

## Goal

Behavior-preserving refactor that makes PacketContext own independently copied per-cell runtime payloads and makes CellContext reference its PacketContext working payload.

## Allowed Paths

- `src/rm_ref/core/lifecycle.py`
- `tests/test_core/test_runner.py`

## Forbidden Paths

- `src/rm_ref/core/config.py`
- `src/rm_ref/core/context.py`
- `src/rm_ref/runtime/`
- `src/rm_ref/config/`
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
- `tests/test_config/`
- `tests/test_integration/`
- `agents/`
- `scripts/`
- `docs/`
- `utils/`
- `schema_defs/`

## Required Checks

- `python -m pytest -q tests/test_core/test_runner.py`
- `python -m pytest -q tests/test_core tests/test_config tests/test_integration`
- `python -m pytest -q`
- `$env:PYTHONPATH='src'; D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q tests/test_core tests/test_config tests/test_integration`
- `$env:PYTHONPATH='src'; D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q`
- `python scripts/agent_workflow.py check-scope`

## Notes

- The RM code baseline is main commit b255977.
- The broad Phase 1 experiment remains preserved on codex/phase1-runtime-contracts at a9281dc and must not be modified, reverted, or extended.
- This task is limited to P1-A1 payload working-copy ownership; do not implement static config or CellContext public API refactors.
- Keep Python 3.6.3 compatibility and add no third-party runtime dependencies.

## Remote Sync

- Remote: `origin`
- URL: `https://github.com/Satahrir/rm_ai_worktree.git`
- Run `python scripts/agent_workflow.py check-sync` before an approved push.
