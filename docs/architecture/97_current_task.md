# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `p3a-python-case-packet-hex-architecture-revision`
- Status: `READY`
- Role: `arch`
- Branch: `codex/arch`
- Worktree: `rm_ref_arch`
- Prompt: `agents/p3a_python_case_packet_hex_arch_revision_prompt.md`

## Goal

Revise the P3A architecture to close the reviewed identity-binding, canonical-ordering, stream-grouping, scalar-type, choices-order, and numeric-helper contract gaps.

## Allowed Paths

- `docs/architecture/`

## Forbidden Paths

- `src/`
- `tests/`
- `utils/`
- `schema_defs/`
- `agents/`
- `scripts/`
- `docs/review/`

## Required Checks

- `python scripts/agent_workflow.py check-scope`

## Notes

- Revise docs/architecture/15_python_case_and_packet_hex_v1.md using the CHANGES REQUIRED review report.
- Close the identity-binding/count-comparison blocker and both major findings.
- Close the bool/scalar, choices ordering, and numeric-helper minor findings.
- Preserve fixed packet-hex v1 encoding and unchanged core/runtime contracts.
- Do not implement code in this task.
