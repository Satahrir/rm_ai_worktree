# src/rm_ref/schema/AGENTS.md

## Role

`rm_ref.schema` owns schema representation, schema normalization, and schema lookup.

A schema describes external interface fields, such as hardware control words, packet header fields, or algorithm-facing configuration fields.

This package should stay independent from the core execution pipeline.

## Main responsibilities

This package may provide:

```text
Field definition object
Schema definition object
Schema registry
Schema normalization helpers
Field lookup helpers
Duplicate field handling
Schema self-consistency checks
```

## Input

Typical input is a plain Python dict, for example:

```python
SCHEMA = {
    "schema_id": "demo1/v1",
    "word_width": 32,
    "word_count": 4,
    "fields": [
        {
            "name": "packet_type",
            "word": 0,
            "msb": 31,
            "lsb": 28,
            "width": 4,
            "enum": {
                "PUSCH": 1,
                "PUCCH": 2,
                "PRACH": 4,
                "SRS": 8,
            },
            "default": "SRS",
            "description": "Packet type field",
        },
    ],
}
```

Generated schemas may come from Excel extraction tools, but this package should not depend on Excel files directly.

## Output

This package should output normalized schema objects or simple objects that can be consumed by:

```text
rm_ref.config
rm_ref.validator
rm_ref.packer
```

## Field metadata

A field descriptor may preserve:

```text
name
normalized_name
original_name
instance
group
word
msb
lsb
width
enum
default
min
max
description
reserved flag
```

Keep enough metadata for useful validation and packing errors.

## Duplicate fields

Duplicate original field names are valid.

For example, an interface table may contain two fields named:

```text
frame_num
frame_num
```

Do not silently drop duplicates.

Instead, preserve enough metadata to distinguish them, such as:

```text
original_name = "frame_num"
name = "header0.frame_num"
instance = 0
group = "header0"

original_name = "frame_num"
name = "header1.frame_num"
instance = 1
group = "header1"
```

Single-instance fields do not need artificial prefixes unless the schema source already provides them.

## Reserved fields

Reserved fields such as `RSV` should be preserved only when useful for word width or packing layout.

They should not normally become required user configuration fields.

The exact reserved-field policy should be explicit and tested.

## Normalization rules

Schema normalization should be deterministic.

Possible normalization behavior:

```text
- preserve original field name
- create a stable normalized name
- compute width from msb/lsb when missing
- verify width equals abs(msb - lsb) + 1
- verify word index is non-negative
- verify bit indices are within word width
- normalize enum keys and values without losing original names
```

Do not invent business semantics during schema normalization.

## Schema registry

A schema registry may support:

```python
registry.register(schema)
registry.get("demo1/v1")
registry.has("demo1/v1")
```

The registry should be explicit.

Avoid hidden global mutable registries unless the user explicitly asks for that behavior.

## Error handling

Schema errors should include:

```text
schema id
field name if available
word index if available
msb/lsb if available
reason
```

Examples:

```text
field packet_type width mismatch: declared width=3 but msb/lsb imply width=4
field n_srs has invalid bit range msb=40 lsb=32 for word_width=32
schema demo1/v1 has duplicate normalized field name frame_num
```

## Forbidden responsibilities

`rm_ref.schema` must not:

```text
create RMContext
run algorithms
drive packet/cell loops
pack hardware words
validate testcase values beyond schema self-consistency
parse full testcase files
load payload data
write result files
depend on rm_ref.core pipeline
```

## Dependency rules

Allowed dependencies:

```text
standard library
typing
local schema modules
```

Avoid depending on:

```text
rm_ref.core.pipeline
rm_ref.core.runner
rm_ref.algorithms
rm_ref.packer implementation details
Excel parser utilities
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

Use normal classes and explicit constructors.

## Tests

Tests belong in:

```text
tests/test_schema/
```

Minimum expected tests:

```text
load schema dict
normalize field width
preserve original field name
handle enum metadata
handle default metadata
detect invalid bit range
detect duplicate normalized names
support duplicate original names with instances
registry register/get/has
reserved field policy
```

## Completion checklist

Before finishing a schema task, check:

```text
pytest -q tests/test_schema
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