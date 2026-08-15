# Python Case And Packet Hex V1 Architecture

## 1. Status

```text
Designed:
  Pure-Python CASE contract, deterministic field randomization, generic
  packet-word contracts, packet-hex v1, manifest, and comparison behavior.

Implemented:
  UserConfig / ResolvedConfig / ConfigResolver / Validator
  run_case(user_config, schema, algorithm, payload_by_packet=None)
  in-memory payload_by_packet injection
  UVM table text/JSON compatibility entry points

Not implemented by this task:
  Python CASE loader and normalizer
  randomizer and provenance manifest
  hardware word packer
  generic packet-word objects
  packet-hex codec
  packet comparison
```

This document is the v1 design target. It does not claim that the designed
interfaces exist in production code. This task changes documentation only.

## 2. Purpose

V1 adds a trusted, pure-Python testcase path and one packet representation that
can be shared by stimulus, intermediate RM data, RM expected output, DUT actual
output, and comparison.

The complete intended preparation and execution flow is:

```text
trusted Python module exporting CASE
  -> CASE shape validation and normalization
  -> deterministic randomization of eligible omitted fields
  -> UserConfig
  -> existing ConfigResolver
  -> existing Validator
  -> optional word packer
  -> PacketBundle containing pure unsigned 32-bit words
  +-> payload_by_packet conversion -> existing run_case()
  `-> packet-hex v1 export -> RTL/UVM-owned file loading

DUT packet-hex v1 output
  -> packet-hex decode
  -> decoded packet ordinals plus pure 32-bit words
  -> bind identities from manifest or expected bundle
  -> PacketBundle containing pure unsigned 32-bit words
  -> structural and word comparison with RM expected PacketBundle
```

The existing UVM table path remains compatible and independent:

```text
uvm_table_printer text or parser JSON
  -> existing UVM adapter boundary
  -> UserConfig
  -> existing run_case()
```

Python testcase scripts do not import, invoke, or depend on the UVM table
parser. Both sources converge at `UserConfig`; neither is the canonical source
for the other.

## 3. V1 Goals And Non-Goals

### 3.1 Goals

- Represent a testcase as auditable Python data exported as `CASE`.
- Preserve explicit values and randomize only explicitly eligible omitted
  fields.
- Produce identical randomized values on every supported platform and Python
  version for the same v1 inputs.
- Keep all in-memory packet data as unsigned 32-bit integers.
- Use one strict, line-oriented packet format at file IO boundaries.
- Reconstruct packet boundaries during import and compare packet structure as
  well as word values.
- Record enough provenance to reproduce every generated field and locate every
  packet in the exported text.
- Keep core config, context, algorithm, and `run_case()` contracts unchanged.

### 3.2 Non-goals

- Loading arbitrary untrusted Python safely or sandboxing testcase code.
- Replacing the UVM table parser or UVM adapter.
- Making SystemVerilog/UVM file loading an RM responsibility.
- Supporting signed field randomization or signed packet words in v1.
- Encoding packet index, cell index, stream role, schema, or seed in packet-hex.
- Supporting an empty packet, a one-word packet, comments, headers, or multiple
  records on one line.
- Defining business-specific conversion from every algorithm output shape to
  packet words.
- Changing `CellContext`, `PacketContext`, `TestcaseConfig`, or `run_case()`.

## 4. Trusted Python CASE Contract

### 4.1 Module boundary

A testcase is a trusted importable Python module. The loader imports it and
requires an attribute named `CASE`; other module attributes are ignored. V1 defines `CASE` as a plain
mapping containing only plain Python scalar, list, and mapping values. Classes,
generators, callbacks, and constraint functions are not part of the v1 data
contract.

Import executes ordinary Python code. Therefore the caller must only load
trusted modules. The loader does not claim to sandbox imports. Import failure,
missing `CASE`, or an invalid `CASE` shape is a case-load/setup error before
`run_case()`.

V1 CASE containers are plain `dict` and `list` objects (not subclasses with
behavior), and every mapping key is a string. A v1 integer is an `int` other
than `bool`. CASE control values (`version`, `master_seed`, indexes, and
constraint bounds/choices) use v1 integers. Strings are permitted where this
contract says a name, enum name, or metadata string; `None` is permitted only
where this contract explicitly uses an absent index. Floats, bytes, tuples,
sets, arbitrary objects, and non-string mapping keys are rejected by CASE
shape validation. A field value may use another scalar type only if the
existing selected schema/resolver contract explicitly accepts that type; CASE
normalization must not introduce a new conversion rule for it.

### 4.2 Required and optional keys

```text
CASE
  version             required; v1 integer 1
  case_name           required; non-empty string
  schema_id           required; non-empty string
  master_seed         required; v1 integer, 0 <= value < 2**64
  algorithm_name      optional metadata; string; default ""
  global_values       optional fixed values; mapping; default {}
  packets             required; non-empty ordered list
  randomizable        optional explicit allowlist; default all scopes empty
  constraints         optional declarative constraint list; default []
  stimulus            optional PacketBundle-shaped mapping
```

Each packet and cell uses the existing user-config concepts:

```text
packet
  packet_index        required non-negative v1 integer
  values              optional fixed packet-scope values
  cells               required non-empty ordered list

cell
  cell_index          required non-negative v1 integer
  values              optional fixed cell-scope values
```

Explicit indexes are required in the Python CASE contract even though the
existing `UserConfig` can infer positional indexes. Stable indexes are needed
for sub-seeds, manifests, payload conversion, and comparison diagnostics.
Packet indexes must be unique. Cell indexes must be unique within a packet.

Field names are normalized through the injected `SchemaDefinition`. Unknown
or ambiguous aliases are setup errors. The normalized field name is used in
seed keys and provenance.

### 4.3 Example CASE

The following example fixes `cell_id=0`, omits fields that are eligible for
randomization, and supplies a two-packet stimulus bundle. Names are illustrative
and must exist in the selected schema.

```python
CASE = {
    "version": 1,
    "case_name": "demo_two_packets",
    "schema_id": "demo_link_v1",
    "master_seed": 0x0123456789ABCDEF,
    "algorithm_name": "demo",
    "global_values": {
        "enable": 1,
    },
    "packets": [
        {
            "packet_index": 0,
            "values": {
                "packet_kind": "DATA",
            },
            "cells": [
                {
                    "cell_index": 0,
                    "values": {
                        "cell_id": 0,
                        # gain and scrambling_id are deliberately omitted.
                    },
                },
            ],
        },
        {
            "packet_index": 1,
            "values": {
                "packet_kind": "DATA",
            },
            "cells": [
                {
                    "cell_index": 0,
                    "values": {
                        "cell_id": 0,
                        # gain and scrambling_id are deliberately omitted.
                    },
                },
            ],
        },
    ],
    "randomizable": {
        "global": [],
        "packet": [],
        "cell": ["gain", "scrambling_id"],
    },
    "constraints": [
        {
            "scope": "cell",
            "field": "gain",
            "packet_index": 0,
            "cell_index": 0,
            "choices": [2, 4, 6],
        },
        {
            "scope": "cell",
            "field": "gain",
            "packet_index": 1,
            "cell_index": 0,
            "minimum": 8,
            "maximum": 12,
        },
    ],
    "stimulus": {
        "role": "stimulus",
        "packets": [
            {
                "packet_index": 0,
                "cell_index": 0,
                "words": [0x01234567, 0x89ABCDEF, 0x00000000],
            },
            {
                "packet_index": 1,
                "cell_index": 0,
                "words": [0xDEADBEEF, 0xCAFEBABE],
            },
        ],
    },
}
```

The `stimulus` section is already packetized data. It is not a replacement for
schema-driven packing. A case may instead omit it and obtain packet words from
the future packer or another caller-owned producer.

## 5. Randomization Policy

### 5.1 Explicit eligibility

V1 is deny-by-default. `randomizable` is an allowlist keyed by schema scope:

```text
randomizable.global
randomizable.packet
randomizable.cell
```

Each value is a list of schema field names or aliases. After normalization, an
omitted field is eligible only when all of the following are true:

1. Its normalized name is allowlisted for its schema scope.
2. It is omitted from the fixed values at that exact scope instance.
3. It is not reserved.
4. It has an integer domain derivable from a matching testcase constraint,
   schema enum, schema min/max, or unsigned width.

A constraint does not implicitly make a field randomizable. It must also be on
the allowlist. An explicit value always remains fixed even if its field is on
the allowlist or has a matching constraint.

Reserved fields never randomize. Their deterministic pack value is owned by
schema/default and packer policy, normally zero. A reserved field in the
allowlist, in constraints, or in explicit CASE values is a setup error rather
than being silently ignored.

V1 does not add a `randomizable` attribute to `FieldDefinition`. If schema
metadata is contradictory, incomplete, or cannot prove a legal unsigned
domain, randomization fails closed for that field: it must not generate a
value. The preparation layer records a diagnostic and then either leaves the
field omitted so an existing schema default can apply, or reports a setup error
when no default exists. Implementations must not guess a range merely to keep
generation running.

### 5.2 Declarative constraints

Each v1 constraint selects exactly one field and zero or one specific packet
and cell instance. Selectors must match the field scope:

```text
global: scope, field
packet: scope, field, packet_index
cell:   scope, field, packet_index, cell_index
```

It then defines exactly one domain form:

```text
choices: non-empty list of distinct v1 integers or enum names

or

minimum and maximum: inclusive integer bounds; both required
```

V1 has no predicate callbacks, weighted values, cross-field constraints, or
retry loops. Multiple constraints targeting the same field instance are an
error. Constraints are converted to numeric values using the same enum-name
rules as normal config resolution and must be a subset of the schema-legal
domain. An empty intersection is an error. Author order is accepted only as
readable CASE input; it is not a sampling rule. After enum conversion, the
distinct numeric values are sorted in numeric order for sampling and for the
reproducibility domain recorded in provenance.

### 5.3 Resolution precedence

For each schema field instance, use this order:

1. **Explicit fixed CASE value.** Preserve it exactly as user input for normal
   resolver conversion and validation. Do not randomize it.
2. **Matching testcase constraint.** If the field is eligible and omitted,
   sample from the declared domain after checking it against schema legality.
3. **Schema random domain.** If eligible and omitted with no testcase
   constraint, sample in this order:
   enum numeric values; inclusive `min..max`; inclusive unsigned-width range
   `0..(2**width - 1)`. When min/max and width both exist, use their
   intersection. Enum values must also satisfy declared min/max and width.
4. **Schema default.** If the field is omitted and has no usable random domain,
   leave it omitted so the existing `ConfigResolver` applies its default.
5. **Error or later validation.** An allowlisted omitted field with neither a
   usable random domain nor a schema default is a randomization setup error. An
   omitted non-randomizable required field without a default remains omitted
   and is reported by the existing validation path.

This ordering means a randomizable omitted field is randomized before a schema
default is considered. To request the default, remove that field from the
allowlist or provide the default explicitly.

Randomization produces a new plain mapping used to construct `UserConfig`.
It must not mutate `CASE`, the schema, or caller-owned values.

### 5.4 Stable per-field sub-seeds

V1 must not use Python `hash()` or depend on iteration order. Every randomized
field instance has an independent seed key:

```text
[
  "rm_ref.field_seed.v1",
  master_seed,
  schema_id,
  stage,
  scope,
  packet_index_or_null,
  cell_index_or_null,
  normalized_field_name
]
```

For config randomization, `stage` is the literal
`"config_randomization_v1"`. Serialize the array with
`json.dumps(value, ensure_ascii=False, separators=(",", ":"))`, encode that
text as UTF-8, and compute SHA-256. JSON `null` represents absent indexes. The
256-bit digest, rendered as 64 lowercase hex digits, is the field sub-seed
recorded in provenance.

Sampling is digest-based so its output does not depend on changes to
`random.Random` across Python versions:

1. Put a candidate domain in canonical order. Integer ranges use numeric order;
   choices and enums are normalized to distinct integers and sorted numerically.
   The recorded sampling domain is this canonical order, never author order.
2. Let `n` be the domain size.
3. Starting at counter zero, compute
   `SHA256(raw_32_byte_field_seed_digest || counter_as_8_byte_big_endian)`.
4. Interpret the digest as an unsigned big-endian integer. Use rejection
   sampling against `floor(2**256 / n) * n`; increment the counter when rejected.
5. Select `candidate % n` from the canonical domain.

This produces an unbiased selection without enumerating a large integer range:
for a range, add the selected offset to the lower bound. Adding, removing, or
reordering an unrelated field does not change another field's value. Changing
the master seed, stable indexes, normalized field name, schema id, or stage does.

## 6. Config Boundary And Diagnostics

The CASE preparation layer receives an already constructed
`SchemaDefinition`. Schema lookup and module-name-to-schema policy remain
caller-owned, matching the current explicit schema injection rule.

```text
CASE mapping + explicit SchemaDefinition
  -> normalize fields and constraints
  -> randomize eligible omissions
  -> UserConfig.from_dict(...)
  -> existing run_case(user_config, schema, algorithm, payload_by_packet=...)
```

The new layer must not modify `ConfigResolver` precedence for existing callers.
It materializes generated values as user values before calling the resolver and
retains separate provenance indicating that they were generated. Existing
`ResolvedConfig.value_sources` may continue to say `user` until a separately
approved source-model extension exists; the manifest is authoritative for CASE
generation provenance.

Case-load and randomization errors should include, when available:

```text
module or source file
case name and schema id
master seed
scope and normalized field name
packet index and cell index
bad value or constraint
expected rule
field sub-seed and sampling stage
```

These failures occur before algorithm execution. The future outer CASE runner
may wrap them as setup errors, but this design does not change
`OrchestrationResult` or `run_case()`.

## 7. Generic Packet-Word Model

### 7.1 Value objects

V1 places the boundary-neutral value contracts in a new `rm_ref.packet`
package, with plain Python 3.6-compatible classes:

```python
class PacketWords(object):
    def __init__(self, packet_index, cell_index, words):
        pass


class PacketBundle(object):
    def __init__(self, role, packets):
        pass
```

This is not part of core. Before implementation, the workflow coordinator must
create a packet-boundary task whose allowed paths include
`src/rm_ref/packet/` and its focused tests. That is a workflow assignment, not
an unresolved data-model decision.

`PacketWords` rules:

- `packet_index` and `cell_index` are explicit non-negative integers.
- `words` is an ordered non-empty sequence of plain integers.
- Each word satisfies `0 <= word <= 0xFFFFFFFF`; `bool` is rejected.
- The constructor copies the sequence; serialization returns fresh plain data.
- V1 packet-hex export additionally requires at least two words.
- No boundary flag is stored in the object.

`PacketBundle.role` is one of these stable strings:

```text
stimulus
intermediate
expected
actual
```

A bundle preserves packet order and requires unique
`(packet_index, cell_index)` identities. The same value types are used at every
stage; the role describes provenance, not a different binary representation.
`PacketBundle` represents exactly one logical stream. It does not represent a
directory, a multi-file artifact, or a physical lane collection.

An interface artifact is an external ordered mapping of named stream/layout
descriptors to one `PacketBundle` and one manifest per stream. Each descriptor
defines its artifact name, stream name, antenna/lane order when applicable,
and its reversible physical layout policy. This metadata belongs to the
interface adapter and its manifest, not to core identity. If one physical file
needs multiple records for the same cell, its adapter must first define a
reversible aggregate word layout and create one v1 `PacketWords` for that cell;
it must not add `stream_id` to `(packet_index, cell_index)` or allow duplicate
identities in a bundle.

Packet words are transport values. They do not expose schema fields and do not
belong in static `CellConfig.parameters`. The existing runtime payload value is
opaque: one `(packet_index, cell_index)` selects one Python value, but that value
may itself contain multiple antennas, lanes, channels, or sample arrays.

For a flat word-oriented interface, the convenience conversion copies `words`
directly into the existing payload mapping:

```python
payload_by_packet = {
    packet.packet_index: {
        packet.cell_index: list(packet.words),
    }
    for packet in stimulus_bundle.packets
}
```

The converter rejects duplicate identities or identities not present in the
resolved case. Missing identities retain the existing `run_case()` behavior:
the corresponding cell receives `[]`.

For example, one cell carrying four antennas may instead receive one logical
structured value:

```python
payload_by_packet = {
    0: {
        0: {
            "antennas": [ant0_samples, ant1_samples, ant2_samples, ant3_samples],
        },
    },
}
```

This remains one runtime payload value for the cell. It is not required to be a
scalar or a single physical stream. The algorithm interprets the structure as
business input through `CellContext`; core and runtime do not interpret its
antenna dimension.

### 7.2 Producer and consumer roles

```text
CASE stimulus or packer
  -> canonical in-memory logical stimulus
     +-> RM payload adapter -> payload_by_packet -> run_case()
     `-> interface layout adapter
          +-> PacketBundle(s)
          `-> packet-hex encoder -> one or more RTL stimulus files

algorithm-specific output adapter
  -> PacketBundle(role="intermediate" or "expected")
  -> packet-hex encoder

DUT output file
  -> packet-hex decoder
  -> decoded packet ordinals and word lists
  -> identity binding from manifest or expected bundle
  -> PacketBundle(role="actual")
  -> comparator against expected bundle
```

For a word-oriented RM input, `payload_by_packet` conversion and RTL text export
must consume the same canonical word sequence: word values, packet boundaries,
and ordering must be identical and come from one generation/packing result.
They need not share the same Python object because boundary code may deep-copy
values. The two paths must not independently randomize or pack nominally equal
inputs. For a semantic or multi-antenna RM input, both the RM payload adapter
and physical-file layout adapter must consume the same canonical logical
stimulus and record the layout policy in provenance. They must not independently
regenerate random stimulus.

An interface layout adapter may serialize four antennas as four named stream
artifacts, each with one bundle/file/manifest, or aggregate the four antennas
reversibly into one logical stream and one bundle/file/manifest. File count,
stream names, antenna order, interleave stride, and per-antenna word packing
are interface policy outside core. They do not require four RM cells or four
`payload_by_packet` entries.

The normal generated-stimulus flow is memory-first: prepare the logical
stimulus once, inject its RM view, and export its RTL view. The RM algorithm does
not read back the text files it just produced. When an external stimulus file
is the original source, IO instead decodes it first into the canonical in-memory
form, after which the same RM payload boundary is used. File IO never moves into
the algorithm or core pipeline.

### 7.3 Shared numeric conversion helpers

Algorithm implementations are expected to consist of small business
submodules. Their outputs are commonly scalar, integer, or complex variables,
not packet words. The business-specific choice of which variables form which
expected or intermediate packet remains deferred to each algorithm adapter.

Common deterministic numeric primitives may be implemented earlier and reused
by those adapters and the packer. Candidate operations are:

```text
saturate_unsigned(value, width)
saturate_signed(value, width)
truncate_unsigned(value, width)
encode_twos_complement(value, width)
quantize(value, fractional_bits, rounding_mode, width, signed)
pack_complex_components(real_value, imag_value, component format and order)
```

Each helper must make width, signedness, rounding, saturation, truncation, and
real/imaginary bit order explicit. It must return an integer or structured
numeric result, never a preformatted hexadecimal string. A complex-to-packet
conversion therefore has two distinct steps:

```text
complex value
  -> explicit quantization/saturation/component packing
  -> unsigned 32-bit integer word
  -> packet-hex codec when text is required
```

V1 does not select one universal complex layout because component widths,
Q-format, rounding, and I/Q order are interface-specific. Generic helpers may
provide the mechanics, while schema or algorithm adapters supply those
policies. Errors and optional debug records should include original value,
selected policy, intermediate quantized values, saturation/truncation events,
and final unsigned word.

These helpers are not part of Slice 1. Before any numeric-helper slice is
implemented, a separate approved contract must define accepted input types,
width bounds, named rounding modes and tie rules, overflow/saturation and
truncation behavior, signedness, component order, and deterministic
known-answer vectors. Implementations must not rely on platform float behavior
where an integer/reference-vector rule has not been specified.

## 8. Packet-Hex V1

### 8.1 Record layout

Each logical line is exactly nine hexadecimal characters:

```text
character:  0         1........8
bits:       35:32     31........0
            00FF      DATA_WORD

bits 35:34 = 00
bits 33:32 = boundary flag
bits 31:0  = unsigned data word
```

Boundary flags are:

```text
00  middle word
01  first word
10  last word
11  forbidden
```

Because bits 35:34 must be zero, the first hexadecimal character is only `0`,
`1`, or `2`; `3` carries the forbidden flag and `4` through `F` have nonzero
reserved bits.

Canonical export uses uppercase hexadecimal, exactly eight digits for data,
no `0x` prefix, and ASCII LF after every record including the final record.
The decoder accepts uppercase or lowercase hexadecimal and LF or CRLF. It may
accept EOF immediately after the ninth character of the final record. A UTF-8
BOM, whitespace, blank line, comment, header, prefix, separator, or trailing
character is invalid.

### 8.2 Packet state machine

Every packet contains at least two words:

```text
outside packet --01/first--> inside packet
inside packet  --00/middle-> inside packet
inside packet  --10/last---> outside packet
```

Consequences:

- A two-word packet is one `first` record followed immediately by one `last`.
- `middle` or `last` outside a packet is invalid.
- `first` while already inside a packet is invalid.
- EOF while inside a packet is invalid.
- Flag `11` is always invalid.
- Empty or one-word `PacketWords` objects are export errors. There is no
  combined first-and-last flag in v1.
- An empty file contains no packets and is a decode error for a required
  packet bundle.

The codec adds flags during export and discards them after reconstructing
packet boundaries during import. It never inserts flags into the 32-bit word
values.

### 8.3 Encoded example

The two packets from the CASE example encode as:

```text
101234567
089ABCDEF
200000000
1DEADBEEF
2CAFEBABE
```

Interpretation:

```text
lines 1..3: packet 0, words 01234567 89ABCDEF 00000000
line  1:    first
line  2:    middle
line  3:    last

lines 4..5: packet 1, words DEADBEEF CAFEBABE
line  4:    first
line  5:    last
```

Packet-hex itself carries no packet or cell indexes. The low-level decoder
therefore returns an ordered codec result containing packet ordinal zero, one,
and so on plus each packet's pure word list; it does not invent identities or
construct a `PacketBundle`. Actual-data identity handling has two explicit
modes:

1. **Actual manifest present.** Bind every decoded ordinal from that actual
   manifest, then construct the actual `PacketBundle`. The manifest packet
   entries must exactly match the decoded packet count and ordinal order; a
   disagreement is an artifact-binding error with manifest and decode context.
2. **No actual manifest.** Compare the identity-free decoded packet count with
   the expected bundle count first. A missing or extra packet returns a
   structured comparison mismatch, not a setup/binding exception. Only when
   the counts match may the expected bundle bind aligned ordinals to
   `(packet_index, cell_index)` identities and construct the actual bundle for
   identity/order/word comparison.

This keeps the strict `PacketWords` identity rule while avoiding hidden index
conventions and preserves packet-count diagnostics when raw actual data has no
metadata.

### 8.4 Malformed examples

```text
001234567
```

Invalid: a middle record cannot start a packet.

```text
101234567
```

Invalid: EOF occurs before a last record, and a one-word packet is forbidden.

```text
101234567
1DEADBEEF
2CAFEBABE
```

Invalid: a new first record occurs while the previous packet is open.

```text
301234567
```

Invalid: flag `11` is forbidden.

```text
401234567
```

Invalid: bits 35:34 are not zero.

```text
0x1234567
```

Invalid: prefixes are forbidden and the record is not nine hexadecimal
characters.

Decode errors must contain:

```text
file path or source label
one-based line number
raw line text without silently trimming it
decoded packet ordinal, if known
word ordinal within the open packet, if known
boundary state and observed flag, if decoded
expected syntax or state transition
```

The raw text should be safely represented with `repr`-style escaping so CR,
tabs, and spaces remain visible. Export errors include packet index, cell index,
word count, bad word ordinal/value, and the v1 rule.

## 9. Separate Manifest

Packet-hex remains minimal. Metadata is stored in a separate, deterministic
JSON manifest, conventionally beside the artifact as
`<packet-hex-name>.manifest.json`. V1 manifest content is:

```json
{
  "manifest_version": 1,
  "case_name": "demo_two_packets",
  "schema_id": "demo_link_v1",
  "master_seed": 81985529216486895,
  "packet_format": "packet-hex-v1",
  "artifact_role": "stimulus",
  "generator": {
    "name": "rm_ref",
    "version": "implementation-version"
  },
  "packets": [
    {
      "ordinal": 0,
      "packet_index": 0,
      "cell_index": 0,
      "first_line": 1,
      "last_line": 3,
      "word_count": 3
    },
    {
      "ordinal": 1,
      "packet_index": 1,
      "cell_index": 0,
      "first_line": 4,
      "last_line": 5,
      "word_count": 2
    }
  ],
  "field_provenance": [],
  "extensions": {}
}
```

Line ranges are one-based and inclusive. They must be contiguous, ordered,
non-overlapping, and consistent with word counts and decoded boundaries.

Every resolved schema field instance gets a provenance entry, including fixed
values and defaults, so reconstruction does not depend on guessing:

```json
{
  "scope": "cell",
  "packet_index": 0,
  "cell_index": 0,
  "field": "cell_id",
  "value": 0,
  "source": "fixed"
}
```

```json
{
  "scope": "cell",
  "packet_index": 0,
  "cell_index": 0,
  "field": "gain",
  "value": 4,
  "source": "testcase_constraint",
  "stage": "config_randomization_v1",
  "field_seed": "64-lowercase-hex-digits",
  "domain": {
    "kind": "choices",
    "values": [2, 4, 6]
  }
}
```

Stable `source` values are:

```text
fixed
testcase_constraint
schema_enum
schema_range
schema_unsigned_width
schema_default
reserved_default
```

Manifest JSON uses sorted object keys, UTF-8, two-space indentation, and LF
line endings. Packet entries retain bundle order; field provenance is sorted by
the explicit tuple below, rather than by comparing nullable indexes directly:

```text
(scope_rank, packet_present_rank, packet_index_or_zero,
 cell_present_rank, cell_index_or_zero, normalized_field_name)

scope_rank:          global=0, packet=1, cell=2
packet_present_rank: absent=0, present=1
cell_present_rank:   absent=0, present=1
```

For an absent index, its paired `*_index_or_zero` component is zero. This fixed
tuple never compares `None` with an integer and is the only provenance order in
v1. Every manifest mapping key, including nested `extensions` keys, is a string;
every manifest value is JSON-compatible before serialization. The canonical
writer uses `json.dumps(..., sort_keys=True, ensure_ascii=False, indent=2)` and
LF line endings. The generator version identifies the producing implementation;
the format and seed algorithm versions remain independently fixed by their
names.

V1 does not require a packet-file hash or CASE-source hash. The required
top-level `extensions` mapping is the reserved compatibility point for later
optional metadata. V1 producers emit an empty mapping. V1 consumers preserve
or ignore unrecognized keys inside `extensions` and must not interpret them as
verified integrity data. A future hash definition must use a namespaced
extension key and specify algorithm, canonicalized bytes, and digest encoding;
it does not require changing packet-hex v1.

## 10. Comparison Contract

Comparison operates only on reconstructed `PacketBundle` objects. It never
compares the 36-bit text records, boundary nibbles, whitespace, or letter case.

The v1 comparator accepts either an identity-bound actual bundle or an
identity-free decoded actual result under the two modes in Section 8.3. With no
actual manifest it first returns a structured packet-count mismatch if decoded
and expected counts differ; it does not attempt identity binding. Otherwise,
after the applicable binding succeeds, it checks in this order:

1. Both bundles have permitted roles (`expected` and `actual`).
2. Packet counts match.
3. Packet identities and order match after manifest binding or aligned expected
   binding.
4. Word counts match for each packet.
5. Every unsigned 32-bit word matches at the same ordinal.

The comparator returns a structured result, not an ambiguous tuple and not
printed text:

```text
PacketComparisonResult
  ok
  expected_packet_count
  actual_packet_count
  packet_results
  diagnostics

PacketComparison
  packet ordinal/index/cell index
  expected and actual word counts
  word mismatches

WordMismatch
  word ordinal
  expected value
  actual value
  xor mask
```

Structural mismatches are first-class diagnostics. The implementation may
continue comparing aligned packet identities to provide useful diagnostics,
but it must never silently zip and discard extra packets or words. Human-readable
reports belong to observability; the comparator returns machine-readable data.

## 11. Ownership And Dependency Direction

### 11.1 Responsibilities

| Concern | Designed owner | Must not own |
|---|---|---|
| Trusted module import and `CASE` extraction | IO/boundary loader | schema lookup policy, algorithm execution |
| CASE shape, fixed values, allowlist, constraints | config | file reports, packet traversal |
| Field normalization and legal domains | schema | random state, packet files |
| Deterministic selection and provenance | config randomization | packing, runtime traversal |
| Resolved values and defaults | existing config resolver | packet boundary flags |
| Semantic field validation | existing validator | bit placement, text encoding |
| Field-to-32-bit-word placement | packer | testcase import, runtime execution |
| `PacketWords` / `PacketBundle` / comparison data | new boundary-neutral packet package | core context or traversal |
| Packet-hex and manifest serialization | IO | algorithms, config resolution |
| Bundle-to-`payload_by_packet` conversion | runtime boundary | file parsing, word packing |
| Cell execution and results | existing core/runtime | packet-hex, randomization |
| Expected-versus-actual comparison | packet comparison service | printing reports |
| Trace/dump/comparison rendering | observability | comparison semantics |
| RTL file consumption | SystemVerilog/UVM environment | Python RM |

The trusted Python loader may use `importlib`, but it passes the extracted plain
mapping into config normalization. Config logic does not import arbitrary files.

### 11.2 Dependency direction

```text
trusted case loader
       |
       v
schema <-> case normalization/randomization -> UserConfig
                                             |
                                             v
                                  existing resolver/validator
                                             |
                                             v
                                           packer
                                             |
                                             v
                                     packet data contracts
                                      /        |        \
                                     v         v         v
                              packet-hex IO  runtime   comparison
                                                |
                                                v
                                      existing run_case/core
```

`rm_ref.packet` must not import core, runtime, config, schema, packer, IO, or
algorithms. IO, packer, runtime boundary adapters, and comparison may depend on
its value contracts. Core remains unaware of the package.

## 12. Error Ownership

```text
module import / missing CASE / non-plain CASE
  case loader error

unknown fields / bad selector / invalid allowlist or constraint
  case normalization or randomization setup error

invalid resolved business value
  existing structured validation issue

overlap / width / non-32-bit packed result
  packing error with field, word, and bit range

invalid PacketWords or duplicate bundle identity
  packet model error

bad line grammar / flag transition / incomplete packet
  packet-hex decode error with file, line, raw text, packet context

empty or one-word packet / invalid word during export
  packet-hex encode error with packet and word context

unknown runtime packet/cell identity
  existing PayloadMappingError -> SETUP_ERROR

packet/word mismatch
  structured comparison diagnostic, not an exception
```

No boundary should catch all exceptions and erase their specific context.

## 13. Staged Implementation And Test Plan

No source implementation is part of P3A. Recommended follow-up slices are:

### Slice 1: Packet value model and packet-hex codec

Ownership must first be assigned for the new `src/rm_ref/packet/` package.
Implement `PacketWords`, `PacketBundle`, the codec's identity-free decoded
result, strict codec state machine, contextual errors, and plain-data
serialization. IO owns file/string adapters and identity binding; packet
contracts own no file IO.

Minimum tests:

```text
32-bit lower and upper boundaries
reject bool, negative, and >32-bit values
two-word and multi-word round trips
two-packet encoded example from this document
uppercase canonical export; lowercase and CRLF import
all malformed examples and every invalid state transition
empty and single-word export rejection
file/line/raw-text/packet context in decode errors
Python 3.6.3 compatibility
```

### Slice 2: Bundle conversion and manifest

Runtime owns a pure bundle-to-`payload_by_packet` adapter without changing
`run_case()`. IO owns deterministic manifest read/write and binding decoded
packet ordinals to packet/cell identities.

Tests cover identity validation, copying/non-mutation, missing payload behavior,
packet ranges, deterministic JSON (including global/null-index provenance),
actual-manifest binding, no-manifest count mismatch as a structured comparison
result, and manifest/hex disagreement.

### Slice 3: CASE normalization and deterministic randomization

Config owns the v1 CASE model, allowlist, constraints, seed derivation,
digest-based sampling, and field provenance. IO owns trusted module import only.

Tests cover precedence, fixed `cell_id=0`, reserved fields, enum/range/width
domains, invalid constraints, stable known-answer seed vectors, field-order
independence, unrelated-field independence, repeated-run identity, manifest
provenance, v1 integer/bool rejection, canonical choices order, and no input
mutation under Python 3.6.3.

### Slice 4: Packer integration

Packer converts validated resolved fields to unsigned 32-bit packet words and
produces its existing planned debug map. Tests cover field placement, width,
reserved values, packet/cell identity, and byte-for-byte agreement between the
bundle sent to runtime conversion and packet-hex export. A focused numeric
utility sub-slice may first implement explicit saturation, truncation,
two's-complement, quantization, and complex-component packing primitives. Its
known-answer tests must cover boundaries, overflow, rounding modes, I/Q order,
and debug metadata; no helper may return formatted hex text.

### Slice 5: Comparison and output adapters

The packet package owns structural/word comparison. Business algorithm packages
own adapters from their output scopes to expected `PacketBundle` objects.
Observability owns text rendering. Tests cover packet count/order, identity,
word count, word values, XOR masks, extra data, and deterministic serialization.

### Slice 6: End-to-end Python case runner

Runtime composes the preceding boundaries around the unchanged `run_case()`.
Integration tests prove:

```text
CASE -> deterministic UserConfig -> validation -> pack/bundle
same stimulus bundle -> payload_by_packet and RTL packet-hex
expected packet-hex + decoded actual -> structured comparison
UVM table entry points remain operational and independent
```

## 14. Python 3.6 Constraints

All future implementations must use normal classes and explicit constructors.
They must not use `dataclasses`, `Protocol`, `Literal`, `TypedDict`, built-in
generic syntax, `X | Y`, `match/case`, or newer-only standard library APIs.
Stable serialization must not depend on mapping insertion order. SHA-256,
explicit sorting, integer arithmetic, and `json.dumps(..., sort_keys=True)` are
available in Python 3.6.3. V1 sort keys use only integers and strings; they
never rely on Python comparing `None` with an integer. `bool` is rejected where
this architecture requires a v1 integer.

## 15. Limitations And Open Questions

### 15.1 Fixed v1 limitations

- Only unsigned integer field domains and unsigned 32-bit packet words are
  supported.
- Constraints cannot relate two fields or call arbitrary Python predicates.
- Packet-hex requires at least two words and carries no identity metadata.
- One runtime packet/cell identity maps to one logical payload value. The value
  may contain multiple antennas, but each physical multi-file or aggregate
  layout requires an interface-specific artifact/stream adapter.
- Large packet files are modeled in memory; streaming APIs are deferred.
- Output-to-word conversion remains algorithm-specific until each algorithm's
  output schema is designed.

### 15.2 Resolved decisions and future extension points

1. `src/rm_ref/packet/` is the designed home of the boundary-neutral packet
   model. The coordinator assigns an implementation task and allowed scope;
   this has no effect on the public data contract.
2. Schema does not gain a `randomizable` property in v1. CASE uses its explicit
   allowlist. Any serious schema-domain conflict fails closed and does not
   randomize the affected field.
3. Manifest hashes are not part of v1. The required empty `extensions` mapping
   preserves a versioned place to add them later.
4. V1 models one logical payload value for each `(packet_index, cell_index)`
   identity. That value may hold all four antennas, for example as a list of
   four sample arrays. An interface adapter decides whether the RTL view uses
   four named stream artifacts or one reversibly aggregated file. A generic
   `stream_id` is unnecessary in RM core; artifact/stream descriptors remain
   external and may use manifest extensions if required.
5. Each business algorithm is composed from smaller submodules whose outputs
   may be ordinary variables. The exact adapter that groups those variables
   into intermediate or expected packet boundaries remains algorithm-specific
   and is intentionally deferred. Shared conversion mechanics such as
   quantization, saturation, truncation, two's-complement encoding, and complex
   component packing may be implemented in advance under the explicit-policy
   rules in Section 7.3.

The remaining future design work is therefore business and physical-layout
adapter policy, not the v1 line encoding, flag values, minimum packet length,
fixed-value precedence, seed derivation, or unchanged runtime contract.
