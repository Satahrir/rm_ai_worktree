# Packer Agent Prompt

## Role

You are the hardware word packer implementation agent.

Your job is to implement deterministic packing from resolved configuration fields into hardware interface words.

The packer is outside the core execution framework.

## Context

The RM framework has separate layers:

```text
schema
  -> config
  -> validator
  -> packer
  -> core execution
```

The packer should consume already resolved and preferably validated values.

It should not run algorithms or drive packet/cell execution.

## Allowed files

You may modify:

```text
src/rm_ref/packer/
tests/test_packer/
docs/architecture/08_packer.md only if it exists and update is necessary
```

You may read but should avoid modifying:

```text
src/rm_ref/schema/
src/rm_ref/config/
src/rm_ref/validator/
```

Avoid modifying:

```text
src/rm_ref/core/
src/rm_ref/algorithms/
utils/
scripts/
schema_defs/
```

unless explicitly asked.

## Primary task

Implement the first version of a word packer.

Required capabilities:

```text
1. Pack one field into one 32-bit word.
2. Pack multiple fields into the same word.
3. Pack fields across multiple words.
4. Validate msb/lsb/width consistency before packing.
5. Reject values that do not fit the declared width.
6. Support enum values that are already numeric.
7. Support defaults when provided by resolved config/schema.
8. Support reserved fields with deterministic zero behavior.
9. Produce an optional debug map.
10. Add focused pytest tests.
```

## Required modules

Implement or refine modules such as:

```text
src/rm_ref/packer/bit_utils.py
src/rm_ref/packer/word_packer.py
src/rm_ref/packer/errors.py
```

Do not create one giant module.

## Packing convention

Use this bit convention:

```text
word is a 32-bit unsigned integer
bit 31 is the most significant bit
bit 0 is the least significant bit
field uses inclusive [msb:lsb]
```

Example:

```text
field packet_type
word = 0
msb = 31
lsb = 28
width = 4
value = 8

packed result:
word0[31:28] = 0b1000
```

## Bit utility behavior

Useful helper functions may include:

```text
compute_width(msb, lsb)
make_mask(msb, lsb)
check_unsigned_fits(value, width)
insert_field(word_value, field_value, msb, lsb)
extract_field(word_value, msb, lsb)
```

Keep these helpers small and well tested.

## Input model

The packer may accept simple field descriptors rather than depending on a complex full ResolvedConfig initially.

A practical first API may look like:

```python
packer = WordPacker(word_width=32, word_count=4)
result = packer.pack_fields(fields, values)
```

or:

```python
words, debug_map = pack_words(schema, resolved_values)
```

Pick a simple explicit API and test it.

## Output model

Return structured output.

Recommended shape:

```text
PackResult
  ok
  words
  debug_map
  errors
```

or raise `PackError` for programmer/setup errors.

For normal invalid user values, structured errors are preferred when practical.

## Debug map

The debug map should be machine-readable.

Possible fields:

```text
field name
word index
msb
lsb
width
value
mask
shift
contribution
final word value
```

Do not print debug information directly from packer functions.

## Value fitting

For unsigned fields:

```text
0 <= value < 2 ** width
```

Reject negative values in the first version unless signed fields are explicitly designed.

Do not silently truncate values.

## Reserved fields

Reserved fields should pack as zero by default.

Reserved fields should not normally require user input.

If a reserved field has a non-zero default, make that behavior explicit and tested.

## Overlap detection

Detect overlapping fields in the same word.

Example:

```text
field_a word0[7:4]
field_b word0[5:0]
```

These overlap at bits `[5:4]` and should report an error unless explicitly allowed.

## Error quality

Packing errors should include:

```text
field name
bad value
word index
msb
lsb
width
reason
```

Good:

```text
field packet_type value=16 cannot fit width=4 at word0[31:28]
```

Bad:

```text
pack failed
```

## Forbidden behavior

Do not:

```text
parse Excel
parse full testcase files
run algorithms
create RMContext
drive packet/cell loops
perform protocol semantic validation beyond bit safety
silently mutate resolved config
introduce Python 3.7+ syntax
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

Use:

```text
normal classes
explicit __init__
typing.Dict
typing.List
typing.Optional
typing.Union
```

## Tests

Add focused tests under:

```text
tests/test_packer/
```

Minimum tests:

```text
test_compute_width
test_make_mask
test_insert_field
test_extract_field
test_pack_single_field
test_pack_multiple_fields_same_word
test_pack_fields_multiple_words
test_reject_value_too_large
test_reject_negative_unsigned_value
test_reject_invalid_bit_range
test_reject_overlapping_fields
test_pack_reserved_field_as_zero
test_debug_map_contains_word_and_bit_info
test_packer_does_not_mutate_input_values
```

## Completion checklist

Before finishing, run:

```bash
pytest -q tests/test_packer
pytest -q
git diff --name-only
git diff --stat
```

If full `pytest -q` fails because other packages are not implemented yet, clearly say so and include focused test results.

Final summary should include:

```text
files changed
packing API implemented
tests run
known limitations
follow-up needed
```