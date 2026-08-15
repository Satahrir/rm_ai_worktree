# Packet Boundary Rules

## Ownership

`rm_ref.packet` owns boundary-neutral packet value objects, strict in-memory
packet encoding/decoding, structured packet comparison data when separately
assigned, and packet-specific errors.

## Dependency Rule

This package must not import core, runtime, config, schema, validator, packer,
IO, observability, algorithms, generated schemas, or utilities. Boundary
packages may depend on `rm_ref.packet`; the reverse is forbidden.

## Data Rule

Internal words are plain unsigned 32-bit integers. Packet boundary flags are
codec metadata and must never be stored in word values. Packet/cell identities
are explicit where the value model requires them; identity-free decoded data
must not invent identities.

## IO Rule

The package may encode/decode in-memory text. It must not open files, create
directories, select artifact names, write manifests, or control RTL/UVM file
loading.

## Python 3.6

Use normal classes, explicit constructors, explicit exceptions, and Python
3.6.3-compatible syntax. Reject bool where an integer is required.

## Tests

Focused tests belong in `tests/test_packet/`. Test value ownership,
serialization independence, exact known-answer encodings, every codec state
transition, and contextual errors.
