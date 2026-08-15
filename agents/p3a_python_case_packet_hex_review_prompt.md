# P3A Python Case And Packet Hex Architecture Review Prompt

## Role

You are the independent review agent for the P3A architecture document. Review
commit `400b431` and write a decision-ready report. Do not edit the architecture
document or implement source code.

## Review Target

Review:

```text
docs/architecture/15_python_case_and_packet_hex_v1.md
```

Write only:

```text
docs/review/p3a_python_case_packet_hex_v1_review.md
```

## Required Review Questions

1. Is the trusted Python `CASE` contract precise, auditable, and compatible
   with `UserConfig`, `ConfigResolver`, `Validator`, and Python 3.6.3?
2. Are fixed-value, randomizable allowlist, constraint, schema-domain, default,
   required-field, and reserved-field precedence rules unambiguous?
3. Is the SHA-256 per-field seed and rejection-sampling algorithm fully
   deterministic without depending on mapping order, Python `hash()`, or
   `random.Random` implementation details?
4. Does the generic packet model correctly preserve `(packet_index,
   cell_index)` identity while remaining independent of stimulus, algorithms,
   core execution, and text IO?
5. Is packet-hex v1 complete and internally consistent: nine hex characters,
   bits 35:34 zero, `00` middle, `01` first, `10` last, `11` forbidden,
   minimum two words per packet, multi-packet files, strict decoder state
   machine, and identity binding outside the raw file?
6. Does the same canonical 32-bit data safely feed RM `payload_by_packet` and
   RTL export without two independent generation or packing paths?
7. Are manifest, comparison, errors, numeric conversion helpers, multi-antenna
   layout boundary, and business output adapters assigned to coherent layers?
8. Does the staged implementation plan respect current repository ownership
   and identify any required new ownership rule for `src/rm_ref/packet/`?
9. Identify contradictions, underspecified API behavior, premature commitments,
   or missing known-answer tests that would block Slice 1 implementation.
10. Confirm the document distinguishes implemented, designed, limitation, and
    future behavior without claiming nonexistent code exists.

## Evidence

Read the current schema/config/runtime contracts and applicable `AGENTS.md`
files. Verify code claims against the repository. Recalculate the packet-hex
examples and inspect the proposed data flow and dependency direction.

This is documentation-only review. Tests are optional unless needed to verify
an implemented claim. Do run:

```powershell
python scripts/agent_workflow.py check-scope
```

## Report Format

Use these sections:

```markdown
# P3A Python Case And Packet Hex V1 Architecture Review

## Verdict
## Evidence Reviewed
## Strengths
## Findings
## Contract Consistency
## Python 3.6 Assessment
## Implementation Readiness
## Recommended Disposition
```

Label findings `BLOCKER`, `MAJOR`, `MINOR`, or `INFO`. State exactly one verdict:
`APPROVE`, `APPROVE WITH FOLLOW-UP`, or `CHANGES REQUIRED`.

## Forbidden Actions

Do not edit production code, tests, schemas, utilities, workflow files,
architecture documents, or existing review reports. Do not merge branches or
update task status.
