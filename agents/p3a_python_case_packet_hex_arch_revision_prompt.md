# P3A Python Case And Packet Hex Architecture Revision Prompt

## Role

You are the architecture agent revising the P3A design after an independent
`CHANGES REQUIRED` review. Update only the existing architecture document. Do
not implement source code or weaken the already agreed packet-hex v1 rules.

## Inputs

Read completely:

```text
docs/architecture/15_python_case_and_packet_hex_v1.md
docs/review/p3a_python_case_packet_hex_v1_review.md
```

## Required Output

Revise:

```text
docs/architecture/15_python_case_and_packet_hex_v1.md
```

## Required Corrections

1. Close the blocker between identity binding and packet-count comparison.
   Define two explicit actual-data modes:
   - actual manifest present: bind decoded ordinals from that manifest, then
     compare count, identity, order, word count, and words;
   - no actual manifest: compare identity-free decoded packet count first and
     return a structured comparison mismatch when it differs; only use the
     expected bundle to bind aligned ordinals when counts match.
   A missing/extra actual packet must not become a setup exception merely
   because no actual manifest exists.
2. Define a Python-3.6-safe canonical provenance sort key. It must never compare
   `None` with integers. Fix scope ranks, presence ranks/sentinels, index order,
   normalized field name order, string-only mapping keys, and JSON-compatible
   manifest values.
3. Make physical stream/artifact grouping explicit. `PacketBundle` represents
   one logical stream with unique `(packet_index, cell_index)` identities. An
   interface artifact is an external ordered mapping of named stream/layout
   descriptors to bundles/manifests. A physical file requiring multiple
   records for one cell must use a reversible aggregate layout adapter rather
   than adding `stream_id` to core identity or permitting duplicate identities.
4. Define v1 integer and scalar rules: integers exclude `bool`; require string
   mapping keys; state permitted scalar/container types for CASE locations;
   reject floats and bytes unless an existing field contract explicitly accepts
   them.
5. Clarify that author order for `choices` is not sampling order. Sampling and
   recorded reproducibility domains use distinct numerically sorted values.
6. Keep generic numeric conversion helpers out of Slice 1. Before their future
   slice, require a separate contract for exact input types, rounding names and
   tie rules, overflow behavior, widths, and deterministic known-answer vectors.

## Preserve

Do not change these fixed v1 decisions:

- internal values are unsigned 32-bit words;
- the IO codec alone adds/removes boundary flags;
- each line is exactly nine hex characters;
- flags are `00` middle, `01` first, `10` last, `11` forbidden;
- every packet contains at least two words;
- raw files contain no metadata, comments, prefixes, or separators;
- `run_case(..., payload_by_packet=...)` and core contracts remain unchanged;
- UVM table input remains independent and supported.

## Implementation Readiness

Retain the recommendation that Slice 1 may implement only packet value objects,
identity-free decoded packets, the strict in-memory codec/state machine,
contextual errors, serialization, and focused tests. Clearly state that Slice 1
requires coordinator ownership for `src/rm_ref/packet/`, while manifests,
identity binding, CASE randomization, runtime conversion, numeric helpers, and
multi-stream layout remain later slices.

## Scope And Completion

Write only under `docs/architecture/`. Run:

```powershell
python scripts/agent_workflow.py check-scope
```

Tests are not required for this documentation-only revision. Report how each
review finding was closed and any genuinely remaining open question.
