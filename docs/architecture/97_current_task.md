# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `core-hardening-v2`
- Status: `READY`
- Role: `core`
- Branch: `codex/core`
- Worktree: `rm_ref_core`
- Prompt: `agents/core_hardening_agent_prompt.md`

## Goal

Harden RM core exception lifecycle finalization and stable result serialization.

## Allowed Paths

- `src/rm_ref/core/`
- `tests/test_core/`

## Forbidden Paths

- `src/rm_ref/schema/`
- `src/rm_ref/config/`
- `src/rm_ref/validator/`
- `src/rm_ref/packer/`
- `src/rm_ref/algorithms/`
- `utils/`
- `schema_defs/`
- `docs/`

## Required Checks

- `python -m pytest -q tests/test_core`
- `python -m pytest -q`
- `python scripts/agent_workflow.py check-scope`

## Notes

- The RM Core Minimal Framework is already implemented and usable.
- Keep fail-fast exception behavior while finalizing all started contexts.
- Preserve existing object APIs while adding deterministic to_dict serialization.
- Fast-forward the existing clean rm_ref_core worktree to the committed main baseline before implementation.
