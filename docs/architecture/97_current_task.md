# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `p1-current-flow-doc`
- Status: `MERGED`
- Role: `arch`
- Branch: `codex/arch`
- Worktree: `rm_ref_arch`
- Prompt: `agents/arch_agent_prompt.md`

## Goal

Document the currently implemented schema-to-result flow and identify the P1 orchestration and integration-test gaps.

## Allowed Paths

- `docs/architecture/`

## Forbidden Paths

- `src/`
- `tests/`
- `utils/`
- `schema_defs/`
- `scripts/`
- `agents/`

## Required Checks

- `python scripts/agent_workflow.py check-scope`

## Notes

- Describe current code and tests, not only intended architecture.
- Distinguish implemented behavior, manual caller responsibilities, limitations, and P1 planned work.
- Document the current lack of a unified resolve-validate-convert-run entry point.
- Do not modify source code or tests in this documentation task.
- Architecture documentation committed as a230f3d in codex/arch and merged into main as ce41a0d.
- Question 1 decided: outer orchestration belongs to rm_ref.runtime with no reverse dependency from core.
- Question 2 decided: expected case outcomes use OrchestrationResult while API misuse and framework bugs continue to raise.
- Question 2 exception ownership is now fully designed: callback trust boundary, lifecycle state, cleanup fail-fast behavior, exception priority, and required fault-injection tests are documented.
- The reviewed source answer is archived as docs/architecture/archive/p1_question2_exception_ownership_answer.txt.
- Questions 3 through 7 remain open and are recorded with project facts, evaluation criteria, ownership, and required tests.
- Payload format remains undecided; only existing input_pkt_by_cc and input.samples behavior is documented as implemented.
- Scope check passed; documentation-only task, so tests were not run.
- The next implementation-ready task is the separately scoped core exception-ownership and lifecycle hardening work.
