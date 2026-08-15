# P3A Python Case And Packet Hex Architecture Prompt

## Role

You are the architecture agent for the next RM input/output milestone. Create
`docs/architecture/15_python_case_and_packet_hex_v1.md`. Record the agreed
pure-Python testcase, deterministic randomization, generic packet-word, and
packet-hex v1 design. Do not implement production code.

## Fixed V1 Decisions

- Preserve UVM table text parsing as a compatible input. Python testcase
  scripts are an independent path.
- A trusted testcase module exports `CASE` with case name, schema id, master
  seed, packet/cell structure, fixed values, and optional constraints.
- Explicit fields stay fixed. Eligible omitted fields randomize from testcase
  constraints or schema enum/min/max/unsigned-width constraints. Reserved
  fields never randomize.
- Define precedence for fixed values, testcase constraints, schema random
  ranges, defaults, and errors. Propose an explicit `randomizable` policy.
- Use deterministic per-field sub-seeds derived from master seed plus stable
  scope/index/field/stage keys. Do not use Python `hash()`.
- Internal data is pure unsigned 32-bit words grouped by packet. Boundary flags
  exist only in the text IO codec.
- Define generic packet-word objects for stimulus, intermediate data, RM
  expected output, DUT actual output, and comparison.
- Packet-hex v1 is exactly 9 hex characters per line: bits 35:34 zero, bits
  33:32 boundary flag, and bits 31:0 data.
- Flags are `00` middle, `01` first, `10` last, `11` forbidden. Every packet
  has at least two words. Empty and single-word packets are export errors.
- A file may contain multiple packets and has no prefix, comments, blank lines,
  or separators. Decode errors include file, line, raw text, and packet context.
- The codec adds flags only on export and removes them on import. Comparison
  uses reconstructed packet structure and pure 32-bit values.
- The same words feed `payload_by_packet` and RTL text export. RM does not own
  SystemVerilog/UVM file loading.
- Define a separate manifest with case, schema, seed, format, packet ranges,
  generator version, and field provenance.

## Required Coverage

Document ownership and dependency direction for case specification,
randomization, config resolution, validation, packing, packet-word data,
packet-hex IO, runtime payload conversion, comparison, and diagnostics. Keep
`run_case(..., payload_by_packet=...)` and core contracts unchanged.

Include a Python `CASE` example with fixed `cell_id=0`, omitted random fields,
a two-packet bundle, encoded lines, malformed examples, field seed provenance,
and a staged implementation/test plan split by ownership.

Write only under `docs/architecture/`. Run
`python scripts/agent_workflow.py check-scope`; tests are not required.
