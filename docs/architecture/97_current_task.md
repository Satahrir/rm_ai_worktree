# Current Task

> Generated from `agents/project_status.json`. Do not edit manually.

## Assignment

- Task: `p3a-python-case-packet-hex-architecture`
- Status: `READY`
- Role: `arch`
- Branch: `codex/arch`
- Worktree: `rm_ref_arch`
- Prompt: `agents/p3a_python_case_packet_hex_arch_prompt.md`

## Goal

Document the v1 architecture for pure-Python testcase definitions, deterministic constrained randomization, generic 32-bit packet words, and the shared 9-hex-character packet file format.

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

- Create docs/architecture/15_python_case_and_packet_hex_v1.md.
- Preserve UVM table text parsing as a compatible input path, not a dependency of Python testcase scripts.
- Internal data uses pure 32-bit words; the IO codec alone adds or removes packet boundary flags.
- Packet-hex v1 uses exactly 9 hex characters per line with flags 00 middle, 01 first, 10 last, and 11 forbidden.
- Every packet has at least two words in v1.
- Document deterministic randomization, manifests, comparisons, ownership, and staged implementation.
- Do not implement code in this task.
