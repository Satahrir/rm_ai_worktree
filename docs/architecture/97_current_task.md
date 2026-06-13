# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `core-exception-ownership-v1`
- Status: `MERGED`
- Role: `core`
- Branch: `codex/core`
- Worktree: `rm_ref_core`
- Prompt: `agents/core_exception_ownership_agent_prompt.md`

## Goal

Implement the designed core exception-ownership and lifecycle cleanup contract with focused fault-injection coverage.

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

- Follow the decided Core Exception Ownership Contract in docs/architecture/14_p1_design_questions.md.
- Keep core status values unchanged and do not add core EXECUTION_ERROR.
- A returned RunResult means lifecycle cleanup completed without framework failure.
- Framework and finalizer failures must propagate rather than becoming RunResult.
- The callback trust-boundary limitation is accepted and must remain documented in behavior and tests.
- Do not modify runtime, schema, config, validator, payload, CLI, workflow, or architecture files.
- Feature implementation committed as 6b9b2cc on codex/core.
- Focused tests passed: 48.
- Full regression tests passed: 132.
- Scope check and git diff check passed.
- Independent review completed with no blocking findings.
- Merged into main as 4dfdab1.
