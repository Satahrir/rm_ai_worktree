# P3A Python Case And Packet Hex V1 Architecture Review

## Verdict

**CHANGES REQUIRED**

The proposed boundaries, packet-hex grammar, and a narrow codec-first Slice 1
are sound.  However, the identity-binding rule prevents the specified comparator
from reporting a packet-count mismatch when an actual artifact has no manifest,
and deterministic manifest ordering is incomplete for global provenance.  These
must be resolved in the architecture document before treating the complete v1
comparison/manifest contract as implementation-ready.  A strictly limited Slice
1 may start after its ownership task is assigned, because it need not implement
the affected binding or manifest behavior.

## Evidence Reviewed

- Commit `400b431` (`Document Python case and packet hex v1 architecture`) and
  its parent `400b431^`; the commit adds only
  `docs/architecture/15_python_case_and_packet_hex_v1.md`.
- The reviewed architecture document, especially Sections 1, 4--15.
- Current `UserConfig`, `ConfigResolver`, `FieldDefinition`, core config, and
  `run_case(user_config, schema, algorithm, payload_by_packet=None)` contracts.
- Current UVM-table runtime boundary and the applicable root, docs, and packer
  instructions.
- The packet-hex encoded example was recalculated: its records have reserved
  bits 35:34 equal to zero and flags `01, 00, 10, 01, 10`; the displayed master
  seed equals decimal `81985529216486895`.

## Strengths

- The status section (lines 3--26) clearly distinguishes designed and
  implemented behavior, and explicitly names unimplemented work.  Limitations
  and future extension points are separately stated in Section 15.
- The CASE contract is deliberately trusted, plain-data only, and rejects
  callbacks/generators as hidden dynamic behavior (lines 101--112).  It uses
  explicit non-negative packet/cell indexes even though existing `UserConfig`
  permits positional inference.
- Fixed values, allowlist eligibility, constraints, schema domain, defaults,
  and errors have a clear intended precedence (lines 309--331).  Reserved
  fields and contradictory schema metadata fail closed rather than being
  silently randomized (lines 256--280).
- The SHA-256 design avoids `hash()` and `random.Random`, serializes an ordered
  seed array as UTF-8 JSON, canonicalizes candidate values numerically, and
  uses rejection sampling.  It is suitable for Python-version-independent
  known-answer vectors once implemented.
- Core, contexts, `run_case()`, and the UVM-table path remain explicitly
  unchanged (lines 56--67, 392--414, and 926--928).  Packet text IO is kept
  out of algorithms/core.
- The canonical-stimulus rule correctly distinguishes the same Python object
  from the same generated content.  It permits one cell payload containing
  multiple antennas while leaving four-file versus interleaved layout to an
  interface adapter (lines 522--543 and 1072--1077).
- Packet-hex v1 is otherwise precise: nine hex characters, reserved bits,
  flags, minimum length, multi-packet state transitions, malformed cases, and
  contextual diagnostics are all defined in Sections 8.1--8.4.

## Findings

### BLOCKER — Expected-bundle identity fallback conflicts with packet-count comparison

- **Section:** 8.3, lines 670--677; Section 10, lines 842--848.
- **Risk:** The decoder is intentionally identity-free.  The document requires
  manifest/expected-bundle identity entries to have the same number and order
  as decoded packets before constructing an actual `PacketBundle`.  If an
  actual file has an extra or missing packet and no actual manifest, binding
  from the expected bundle fails before the comparator can perform its required
  packet-count check.  This contradicts the comparison contract and turns a
  structured mismatch into a setup/binding failure.
- **Recommended correction:** Define two explicit modes.  With an actual
  manifest, bind every decoded ordinal using that manifest, then compare
  identities/count/order.  With an expected-bundle fallback, first compare
  identity-free decoded packet count (and optionally aligned ordinals); only
  bind when counts match.  Specify the structured diagnostic/result for each
  mode and state that a count mismatch is a comparison result, not a binding
  exception.
- **Blocks Slice 1:** No.  It blocks Slice 2 manifest/binding and Slice 5
  comparison implementation.

### MAJOR — Manifest provenance order is not fully canonical across Python 3.6

- **Section:** 9, lines 780--827.
- **Risk:** Provenance includes global entries, whose packet/cell indexes are
  absent (`null`), while packet/cell entries have integers.  “Sorted by ...
  packet index, cell index” does not define an ordering between `null` and an
  integer.  Python 3 cannot compare `None` and `int`; different ad-hoc sort
  keys would produce different bytes and break deterministic manifests.
- **Recommended correction:** Define an explicit serialization sort tuple, for
  example `(scope_rank, packet_present, packet_index_or_zero, cell_present,
  cell_index_or_zero, normalized_field_name)`, with `scope_rank` fixed as
  global/packet/cell.  State that all manifest mapping keys, including nested
  `extensions`, must be strings and values JSON-compatible before
  `sort_keys=True` serialization.
- **Blocks Slice 1:** No.  It blocks deterministic manifest implementation in
  Slice 2 and provenance validation in Slice 3.

### MAJOR — PacketBundle is not explicit about physical stream/artifact grouping

- **Section:** 7.1--7.2, lines 457--459 and 502--536; Section 15.2(4).
- **Risk:** A bundle forbids duplicate `(packet_index, cell_index)` identities,
  while an interface may create several antenna/lane streams for one logical
  cell.  The text says four files may use one bundle per file, but does not
  define the artifact-to-bundle mapping, its identity label, or how a single
  physical file containing several per-cell streams is represented without
  duplicate identities.  Implementers could incorrectly add `stream_id` to
  core identity or use one bundle for incompatible physical layouts.
- **Recommended correction:** State that `PacketBundle` is a single logical
  stream with unique cell identities; an interface artifact is an external
  ordered mapping of named stream/layout descriptors to bundles and manifests.
  If a physical file needs multiple records for one cell, require its interface
  adapter to define a reversible aggregate word layout before creating a v1
  `PacketWords`, rather than weakening PacketBundle identity.
- **Blocks Slice 1:** No, provided Slice 1 stays identity-neutral for decoded
  data and does not add multi-stream policy.

### MINOR — CASE integer fields need explicit boolean and scalar-type rejection

- **Section:** 4.2 and 5.2, lines 116--127 and 293--307.
- **Risk:** In Python 3.6, `bool` is an `int` subclass.  Without an explicit
  rule, `master_seed`, indexes, bounds, choices, and field numeric values may
  accept `True`/`False`, yielding surprising seeds/domains.  “Plain scalar”
  also does not define whether float, bytes, tuple, or non-string mapping keys
  are legal in CASE data.
- **Recommended correction:** Define v1 integer as `int` excluding `bool`,
  require string keys for every CASE/manifest mapping, and list permitted
  scalar types per CASE location.  Reject floats/bytes unless a field's existing
  schema conversion explicitly accepts them.
- **Blocks Slice 1:** No.

### MINOR — “ordered choices” conflicts with canonical numeric sampling order

- **Section:** 5.2 line 296; Section 5.4 lines 364--365.
- **Risk:** Calling input `choices` “ordered” suggests author order can affect
  selection, while the sampler must sort normalized numeric values.  This
  ambiguity could create incompatible implementations and vectors.
- **Recommended correction:** Say author order is accepted only for readable
  input and provenance; selection always uses the distinct numerically sorted
  canonical domain, which is also what must be recorded for reproducibility.
- **Blocks Slice 1:** No.

### MINOR — Generic numeric helpers are intentionally deferred but lack a v1 input domain

- **Section:** 7.3, lines 552--581.
- **Risk:** The helpers list operations but does not yet define accepted numeric
  representations or legal rounding-mode identifiers.  Implementing them as a
  generic early utility could accidentally introduce float/platform behavior.
- **Recommended correction:** Keep them out of Slice 1.  Before the numeric
  sub-slice, define exact input types, rounding-mode names/tie rules, overflow
  behavior, width bounds, and integer-only/reference-vector requirements.
- **Blocks Slice 1:** No.

## Contract Consistency

The CASE-to-`UserConfig` boundary is feasible with the existing resolver:
generated values are materialized as user values and existing defaults still
apply.  The proposed provenance source distinction is correctly external to
the current `ResolvedConfig.value_sources` contract.  The design also correctly
keeps opaque `payload_by_packet` values outside static configuration and allows
one structured multi-antenna payload per cell.

Packet-hex record grammar and the example are internally consistent.  Flags do
not contaminate the uint32 word, and packet ordinal is appropriately separated
from packet/cell identity.  The blocker above is the remaining identity-binding
closure for count-mismatched actual data.  Packet words, logical payloads, and
physical files are mostly separated; the physical artifact grouping correction
will make that separation enforceable rather than implicit.

## Python 3.6 Assessment

The designed class style and the named prohibited syntax/APIs are compatible
with Python 3.6.3.  SHA-256, UTF-8 encoding, integer arithmetic, JSON, and
explicit sort keys are available.  The seed array avoids mapping-order
dependence.  The remaining Python 3.6 concern is specifying sort keys that do
not compare `None` with integers and rejecting `bool` where an integer is
required; both are document corrections, not current source failures.

## Implementation Readiness

Recommended first implementation slice: keep Section 13 Slice 1 limited to
`PacketWords`, `PacketBundle`, identity-free decoded packets, in-memory codec
encode/decode, state-machine errors, and plain-data serialization.  Assign a
dedicated packet-boundary task for `src/rm_ref/packet/` and focused tests before
writing code.  Do not include manifests, identity binding, CASE randomization,
runtime conversion, packer integration, algorithm adapters, or multi-antenna
layout policy.

Required Slice 1 known-answer coverage: uint32 boundaries and bool rejection;
two-word/multi-word and two-packet example round trips; all illegal state
transitions/records; canonical upper-case encoding; lower-case and CRLF decode;
and diagnostic context.  Later tests must add fixed SHA-256 seed/sample vectors,
unicode normalized-name vectors, range endpoints, non-divisor rejection cases,
manifest null-index ordering, count-mismatched actual files with and without an
actual manifest, identity/order/extra-data comparison, and artifact-level
multi-antenna layout vectors.

## Recommended Disposition

**CHANGES REQUIRED.** Correct the identity-binding/comparison contradiction and
the canonical manifest ordering before implementing their slices.  After the
workflow assigns ownership for `src/rm_ref/packet/`, starting the narrowly
scoped codec/value-model Slice 1 is recommended; it can remain fully testable
and does not require the unresolved policies.
