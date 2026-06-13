# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `core-cleanup-stack-declaration-v1`
- Status: `MERGED`
- Role: `core`
- Branch: `codex/core`
- Worktree: `rm_ref_core`
- Prompt: `agents/core_exception_ownership_agent_prompt.md`

## Goal

Declare the lifecycle cleanup stack on RMContext so static analysis recognizes the framework-owned runtime attribute.

## Allowed Paths

- `src/rm_ref/core/`
- `tests/test_core/`

## Forbidden Paths

- `src/rm_ref/schema/`
- `src/rm_ref/config/`
- `src/rm_ref/validator/`
- `src/rm_ref/packer/`
- `src/rm_ref/algorithms/`
- `src/rm_ref/io/`
- `src/rm_ref/observability/`
- `tests/test_schema/`
- `tests/test_config/`
- `tests/test_validator/`
- `utils/`
- `schema_defs/`
- `docs/`
- `scripts/`
- `agents/`

## Required Checks

- `python -m pytest -q tests/test_core`
- `python -m pytest -q`
- `python scripts/agent_workflow.py check-scope`

## Notes

- Declare RMContext._cleanup_stack during construction without importing lifecycle.py into context.py.
- Preserve existing cleanup ownership and exception behavior.
- Keep the change limited to core context declaration and focused coverage.
- Do not modify runtime, schema, config, validator, payload, CLI, workflow, or architecture files from the feature worktree.
- Feature implementation committed as 1b00c8b on codex/core.
- Focused core tests passed: 49.
- Full regression tests passed: 133.
- Scope check and git diff check passed.
- Review completed with no blocking findings.
- Merged into main as cca9674.
