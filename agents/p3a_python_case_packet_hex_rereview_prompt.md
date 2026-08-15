# P3A Python Case And Packet Hex Architecture Re-review Prompt

## Role

You are the independent re-review agent for the revised P3A architecture.
Review commit `14410a4` against the original architecture and the first review.
Do not edit architecture or source code.

## Inputs

Read completely:

```text
docs/architecture/15_python_case_and_packet_hex_v1.md
docs/review/p3a_python_case_packet_hex_v1_review.md
```

Inspect the diff `14410a4^..14410a4` and verify each correction against current
repository contracts.

## Required Output

Write only:

```text
docs/review/p3a_python_case_packet_hex_v1_rereview.md
```

## Closure Checks

1. Verify the no-actual-manifest path returns structured packet-count mismatch
   before identity binding, while actual-manifest disagreement remains a
   contextual artifact-binding error.
2. Verify canonical provenance ordering is fully specified for global, packet,
   and cell entries without Python 3.6 `None`/integer comparison, including
   string-only mapping keys and JSON-compatible values.
3. Verify `PacketBundle` is one logical stream and physical multi-stream/file
   grouping remains an external reversible interface-artifact policy without
   weakening `(packet_index, cell_index)` identity.
4. Verify v1 integer excludes `bool` and CASE scalar/container/key rules are
   sufficiently explicit and compatible with existing schema conversion.
5. Verify choices author order cannot affect sampling or recorded domains.
6. Verify numeric helpers remain outside Slice 1 and require a separate exact
   numeric/rounding contract before implementation.
7. Confirm the revision did not change the fixed packet-hex grammar, minimum
   packet length, unchanged `run_case()` contract, or UVM-table independence.
8. Decide whether Slice 1 is implementation-ready with scope limited to packet
   value objects, identity-free codec/state machine, errors, serialization, and
   focused tests.

## Report

Use severity labels `BLOCKER`, `MAJOR`, `MINOR`, and `INFO`. State exactly one
verdict: `APPROVE`, `APPROVE WITH FOLLOW-UP`, or `CHANGES REQUIRED`. Include a
six-item closure table mapping every first-review finding to `CLOSED` or
`OPEN`, with evidence.

This is documentation-only review; tests are optional. Run:

```powershell
python scripts/agent_workflow.py check-scope
```

## Forbidden Actions

Do not edit source, tests, schemas, utilities, workflow files, architecture
documents, or either existing review report. Do not merge or update status.
