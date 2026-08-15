# P3A Python Case And Packet Hex V1 Architecture Re-review

## Verdict

**APPROVE WITH FOLLOW-UP**

Revision `14410a4` closes all six findings from the first review.  The narrow
Slice 1 is ready to begin after the coordinator assigns the dedicated
`src/rm_ref/packet/` ownership/task.  The remaining follow-up is a nonblocking
wording cleanup in the comparison section.

## Evidence Reviewed

- Commit `14410a4` relative to `14410a4^`.
- The revised `docs/architecture/15_python_case_and_packet_hex_v1.md`.
- The first review, `docs/review/p3a_python_case_packet_hex_v1_review.md`.
- Current `UserConfig`, `ConfigResolver`, `FieldDefinition`, core contracts,
  runtime `run_case()`, and the existing UVM-table boundary.

## First-review Finding Closure

| Original finding | Status | Evidence |
|---|---|---|
| BLOCKER: expected-bundle fallback prevented packet-count comparison | **CLOSED** | Section 8.3 now defines actual-manifest and no-actual-manifest modes. The no-manifest mode compares identity-free decoded count before binding and requires a structured mismatch on a difference; actual-manifest disagreement remains a contextual artifact-binding error. Section 10 follows the same sequence. |
| MAJOR: provenance sort could compare `None` and `int` | **CLOSED** | Section 9 defines `(scope_rank, packet_present_rank, packet_index_or_zero, cell_present_rank, cell_index_or_zero, normalized_field_name)`, including ranks/sentinels. It also requires string mapping keys and JSON-compatible values before canonical JSON serialization. |
| MAJOR: physical stream/artifact grouping was implicit | **CLOSED** | Section 7 states that `PacketBundle` is one logical stream; an external ordered artifact descriptor maps named streams/layouts to bundles and manifests. Reversible aggregation is required instead of duplicate identities or a core `stream_id`. |
| MINOR: boolean/scalar/container rules were incomplete | **CLOSED** | Section 4 defines a v1 integer as `int` excluding `bool`, requires plain `dict`/`list` and string keys, and rejects unspecified floats, bytes, tuples, sets, objects, and non-string keys while deferring accepted field values to the existing schema/resolver contract. |
| MINOR: author ordering of `choices` was ambiguous | **CLOSED** | Section 5 makes author order readable input only; enum-converted distinct numeric values are sorted numerically for both sampling and recorded reproducibility domains. |
| MINOR: numeric helpers could be prematurely implemented | **CLOSED** | Section 7 explicitly excludes them from Slice 1 and requires a separate approved contract for types, widths, rounding/ties, overflow, signedness, component order, and known-answer vectors. |

## Contract and Boundary Assessment

The revision preserves the fixed packet-hex v1 grammar: nine hexadecimal
characters; bits 35:34 zero; flags `00` middle, `01` first, `10` last, and
`11` forbidden; and a minimum of two words per packet.  It does not change the
uint32 internal word rule, codec-only boundary flags, unchanged
`run_case(user_config, schema, algorithm, payload_by_packet=None)` contract,
or independent UVM-table input path.

The no-manifest count path now has an explicit identity-free phase. This is the
necessary exception to normal identity-bound comparison and prevents missing or
extra actual packets from being misclassified as setup failures. It leaves
core, runtime traversal, and algorithm/file-IO boundaries unchanged.

## Python 3.6 Assessment

The revised constraints use Python 3.6-compatible concepts and specifically
eliminate the prior unsafe `None`/integer sorting possibility. The v1 integer
rule also addresses Python's `bool`-is-`int` behavior. Canonical JSON uses
explicit sort keys and JSON-compatible values, with no reliance on dictionary
insertion order or `random.Random` behavior.

## Follow-up

- **MINOR:** Section 10 still opens with “Comparison operates only on
  reconstructed `PacketBundle` objects,” while the next paragraph correctly
  permits an identity-free decoded actual result for the no-manifest count
  check. Replace “only” with wording that makes this pre-binding count phase
  explicit. This is editorial consistency only; the detailed operational rule
  is unambiguous and Slice 1 does not implement comparison.

## Slice 1 Readiness

**Ready to start.** Limit implementation to `PacketWords`, `PacketBundle`, an
identity-free decoder result, strict in-memory packet-hex codec/state machine,
contextual errors, plain-data serialization, and focused tests. The coordinator
must first assign ownership for `src/rm_ref/packet/`. Do not include manifests,
identity binding, CASE randomization, runtime conversion, numeric helpers, or
multi-stream layout policy in Slice 1.

## Recommended Disposition

**APPROVE WITH FOLLOW-UP.** All six original findings are closed. Perform the
single comparison-wording cleanup with the next documentation update; it is not
a prerequisite for the narrow Slice 1 implementation.
