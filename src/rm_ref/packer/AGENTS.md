# src/rm_ref/packer/AGENTS.md

## Role

`rm_ref.packer` packs resolved and validated configuration fields into hardware interface words.

It is a boundary between software configuration and hardware-facing bit layout.

The packer should be deterministic, testable, and independent from algorithm execution.

## Main responsibilities

This package may define:

```text
bit utility functions
word packing functions
field-to-bit placement logic
packing result object
packing error classes
optional debug map
```

## Input

Typical input:

```text
ResolvedConfig
normalized schema fields
```

A field definition should contain enough information for packing:

```text
field name
word index
msb
lsb
width
value
enum value if applicable
reserved flag if applicable
default value if applicable
```

## Output

Typical output:

```text
list of 32-bit integer words
optional debug map
structured packing errors
```

Example debug map:

```text
packet_type:
  word = 0
  msb = 31
  lsb = 28
  width = 4
  value = 8
```

## Packer vs Validator

Keep responsibilities separate.

Validator checks semantic correctness.

Packer checks bit placement and bit-width safety.

Example:

```text
Validator:
  c_srs must be in the allowed protocol range.

Packer:
  c_srs value must fit in the declared field width.
```

Some overlap is acceptable, but the primary responsibility should remain clear.

## Required behavior

The packer should support:

```text
word index
msb/lsb bit range
width check
integer values
enum values already converted to numeric form
default values
reserved fields
duplicate field instances
debug map generation
```

## Bit numbering

Use a clear convention.

Recommended convention:

```text
word is a 32-bit unsigned integer
bit 31 is the most significant bit
bit 0 is the least significant bit
field mask is built from msb/lsb
```

Example:

```text
word = 0
msb = 31
lsb = 28
width = 4
value = 8

packed word bits[31:28] = 0b1000
```

## Value range

Before packing, check that the value fits in the declared width.

For unsigned fields:

```text
0 <= value < 2 ** width
```

Signed fields are not required in the first version unless explicitly requested.

If signed packing is introduced later, it must be documented and tested separately.

## Reserved fields

Reserved fields should usually pack as zero unless the schema explicitly provides a different default.

Reserved fields should not normally require user input.

Reserved field policy must be deterministic and tested.

## Duplicate fields

Duplicate original field names are valid if the schema provides distinct normalized names or instance metadata.

Do not silently overwrite values.

Packing should use stable normalized names or explicit field descriptors.

## Error information

Packing errors should include:

```text
schema id if available
field name
original field name if available
bad value
word index
msb
lsb
width
reason
```

Good error example:

```text
field packet_type value=16 cannot fit width=4 at word0[31:28]
```

Bad error example:

```text
pack failed
```

## Debug output

A debug map is useful for hardware verification.

It may include:

```text
field name
word index
msb
lsb
width
input value
masked value
shifted value
final word contribution
```

The debug map should be machine-readable.

Avoid printing directly from packer functions.

## Forbidden responsibilities

`rm_ref.packer` must not:

```text
parse Excel files
parse full testcase files
run algorithms
drive packet/cell loops
create RMContext
load payload data
create result directories
perform business validation beyond bit safety
mutate resolved config silently
```

## Dependency rules

Allowed dependencies:

```text
rm_ref.schema
rm_ref.config
standard library
typing
```

Avoid depending on:

```text
rm_ref.core.pipeline
rm_ref.core.runner
rm_ref.algorithms
Excel parser utilities
UVM tools
```

## Python 3.6 compatibility

Do not use:

```text
dataclasses
TypedDict
Protocol
Literal
list[str]
dict[str, int]
X | Y
match/case
```

Use normal classes, explicit constructors, and `typing.List` / `typing.Dict`.

## Tests

Tests belong in:

```text
tests/test_packer/
```

Minimum expected tests:

```text
pack single field into word
pack multiple fields into one word
pack fields across multiple words
reject value that does not fit width
reject invalid msb/lsb range
pack enum numeric value
pack default value
handle reserved field
preserve duplicate field instances
produce debug map
do not mutate resolved config
```

## Completion checklist

Before finishing a packer task, check:

```text
pytest -q tests/test_packer
pytest -q tests/test_schema
pytest -q tests/test_config
git diff --name-only
git diff --stat
```

Summarize:

```text
files changed
tests run
known limitations
follow-up needed
```