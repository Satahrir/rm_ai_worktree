# Packet Boundary Agent Prompt

## Role

You own the boundary-neutral packet value model and the strict in-memory
packet-hex v1 codec. Implement only Slice 1 from the approved architecture.

## Required Design Sources

Read completely:

```text
docs/architecture/15_python_case_and_packet_hex_v1.md
docs/review/p3a_python_case_packet_hex_v1_review.md
docs/review/p3a_python_case_packet_hex_v1_rereview.md
src/rm_ref/packet/AGENTS.md
tests/AGENTS.md
```

## Required Implementation

Implement under `src/rm_ref/packet/`:

- `PacketWords`: explicit non-negative packet/cell indexes, copied ordered
  uint32 words, bool rejection, deterministic plain-data serialization;
- `PacketBundle`: stable role, ordered copied packets, unique
  `(packet_index, cell_index)` identities, deterministic serialization;
- identity-free decoded packet/result objects containing packet ordinal and
  pure uint32 words but no invented packet/cell identities;
- strict in-memory packet-hex v1 encode/decode and explicit contextual errors;
- a small explicit public import surface in `rm_ref.packet`.

Packet-hex v1 rules:

```text
exactly 9 hexadecimal characters per record
bits 35:34 = 0
bits 33:32 = 00 middle, 01 first, 10 last, 11 forbidden
bits 31:0 = unsigned 32-bit data
each exported packet contains at least two words
one file/text may contain multiple packets
canonical output is uppercase ASCII with LF after every record
decoder accepts uppercase/lowercase and LF/CRLF
no BOM, prefix, whitespace, blank lines, comments, headers, or separators
```

The decoder state machine must reject middle/last outside a packet, first
inside a packet, forbidden/reserved flags, malformed length/hex, incomplete
EOF, and empty input. Decode errors include source label, one-based line,
escaped raw text, decoded packet ordinal when known, word ordinal when known,
state/flag when known, and expected rule. Encode errors include packet/cell
identity, word count, and bad word ordinal/value where applicable.

## Tests

Add focused tests under `tests/test_packet/` for:

- uint32 bounds and bool/negative/overflow rejection;
- copying and non-mutation;
- duplicate identities and role validation;
- deterministic independent `to_dict()` results;
- two-word, multi-word, and multi-packet known-answer encoding;
- uppercase/LF canonical output;
- lowercase, CRLF, and final-record-without-newline decode;
- every invalid grammar/state transition and contextual error fields;
- empty and single-word export rejection;
- Python 3.6.3 compatibility.

## Explicit Non-Goals

Do not implement filesystem IO, manifests, identity binding, expected/actual
comparison, CASE loading/randomization, runtime conversion, packer integration,
numeric helpers, multi-stream layout, algorithms, or core changes.

## Python 3.6

Use normal classes and explicit constructors. Do not use dataclasses, Protocol,
Literal, TypedDict, built-in generic annotations, union operators, match/case,
or newer-only APIs.

## Completion

Run all checks from the active task and `python scripts/agent_workflow.py
check-scope`. Report files changed, APIs, tests, failures, limitations, and
follow-up. Do not commit unless explicitly requested.
