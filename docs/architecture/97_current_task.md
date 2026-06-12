# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `p1-current-flow-doc`
- Status: `IN_PROGRESS`
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
- Baseline document committed as 5f8ce09 in codex/arch.
- Revise the payload boundary: payload_by_packet maps packet_index and cell_index to raw payload.
- The outer runner only fills PacketConfig.input_pkt_by_cc and does not define samples, iq, bits, channel, or antenna payload formats.
- The core pipeline and CellContext remain responsible for exposing the existing input.samples runtime key.
