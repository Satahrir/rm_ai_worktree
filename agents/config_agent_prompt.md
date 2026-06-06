# Config Agent Prompt

## Role

You are the schema/config/validator implementation agent.

Your job is to implement the first version of the input preparation flow:

```text
schema dict
  -> schema object / registry
  -> UserConfig
  -> ResolvedConfig
  -> Validator
```

This flow prepares deterministic configuration before core RM execution.

## Context

This project is a clean rebuild of a Python Reference Model framework.

The old document under `docs/reference/` is reference material only.

Use it to understand why schema/config/validator should stay outside the core execution pipeline.

Do not copy old import paths or old implementation details blindly.

## Allowed files

You may modify:

```text
src/rm_ref/schema/
src/rm_ref/config/
src/rm_ref/validator/
schema_defs/
tests/test_schema/
tests/test_config/
tests/test_validator/
```

You may make tiny testability changes to:

```text
pytest.ini
setup.py
```

only when required.

Avoid modifying:

```text
src/rm_ref/core/
src/rm_ref/packer/
src/rm_ref/algorithms/
docs/
utils/
scripts/
```

unless explicitly asked.

## Primary task

Implement the first testable schema/config/validator flow.

Required capabilities:

```text
1. Load or consume a plain Python schema dict.
2. Convert schema fields into normalized field objects.
3. Register and fetch schema by schema_id.
4. Represent user-provided packet/cell config.
5. Resolve user config into deterministic resolved config.
6. Apply schema defaults.
7. Convert enum names into numeric values.
8. Validate required/min/max/enum/bit-width constraints.
9. Return structured validation results.
10. Add focused pytest tests.
```

## Required modules

Implement or refine modules such as:

```text
src/rm_ref/schema/field.py
src/rm_ref/schema/registry.py
src/rm_ref/schema/normalize.py
src/rm_ref/schema/errors.py

src/rm_ref/config/user_config.py
src/rm_ref/config/resolved_config.py
src/rm_ref/config/resolver.py
src/rm_ref/config/errors.py

src/rm_ref/validator/rules.py
src/rm_ref/validator/validator.py
src/rm_ref/validator/errors.py
```

Do not create one giant module.

## Schema model

A schema should be able to consume a dict like:

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

A field object should preserve useful metadata:

```text
name
normalized_name
original_name
word
msb
lsb
width
enum
default
min
max
description
instance
group
reserved flag
```

## Schema registry

Provide a small explicit registry.

Possible API:

```python
registry = SchemaRegistry()
registry.register(schema)
schema = registry.get("demo1/v1")
exists = registry.has("demo1/v1")
```

Avoid hidden global mutable registries unless explicitly requested.

## UserConfig model

UserConfig represents what the user wrote.

Recommended hierarchy:

```text
UserConfig
  case_name
  algorithm_name
  schema_id
  global_values
  packets[]

UserPacketConfig
  packet_index
  values
  cells[]

UserCellConfig
  cell_index
  values
```

Keep it simple.

Do not put runtime algorithm state into UserConfig.

## ResolvedConfig model

ResolvedConfig represents what the framework will actually use.

Recommended hierarchy:

```text
ResolvedConfig
  case_name
  algorithm_name
  schema_id
  global_values
  packets[]

ResolvedPacketConfig
  packet_index
  values
  cells[]

ResolvedCellConfig
  cell_index
  values
  value_sources
```

`values` should contain normalized field names and final numeric values where possible.

`value_sources` may record:

```text
user
schema_default
resolver_default
```

## Resolver behavior

Resolver should perform:

```text
schema lookup
field-name normalization
default application
enum name-to-value conversion
packet/cell structure preservation
deterministic resolved config creation
```

Resolver should not silently accept bad input.

Examples:

```text
packet_type = "SRS" -> packet_type = 8
missing field with default -> value explicitly present in ResolvedConfig
unknown enum name -> resolver error or validation error with clear message
```

## Validation behavior

Validator should check:

```text
required fields
min/max
enum membership
bit width
integer type where required
custom cross-field rule hook
```

Validation should return a structured result:

```text
ValidationResult
  ok
  errors[]
  warnings[]
```

Normal user mistakes should usually be collected as validation errors, not crash the program.

Programmer errors may raise exceptions.

## Error quality

Errors should include:

```text
schema id
field name
packet index if available
cell index if available
bad value
expected rule
word index if available
bit range if available
```

Good:

```text
schema demo1/v1 packet 0 cell 1 field packet_type value='ABC' is not in enum {PUSCH, PUCCH, PRACH, SRS}
```

Bad:

```text
invalid config
```

## Conversion to core config

Do not focus on full core integration in the first task.

A minimal conversion helper may be added only if needed by tests.

Preferred direction:

```text
ResolvedConfig
  -> core.TestcaseConfig
```

This conversion must not run algorithms.

It should only create static core config.

## Forbidden behavior

Do not:

```text
run algorithms
drive packet/cell execution
pack hardware words
parse Excel files
load payload data
create RMContext during validation
write result directories
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
tests/test_schema/
tests/test_config/
tests/test_validator/
```

Minimum schema tests:

```text
test_schema_from_dict
test_field_width_from_msb_lsb
test_invalid_bit_range_reports_error
test_registry_register_get_has
test_enum_metadata_preserved
```

Minimum config tests:

```text
test_user_config_constructs_packet_cell
test_resolver_applies_default
test_resolver_converts_enum_name_to_value
test_resolver_preserves_numeric_enum_value
test_resolver_preserves_packet_cell_structure
test_resolver_does_not_mutate_user_config
```

Minimum validator tests:

```text
test_valid_config_ok
test_missing_required_reports_error
test_min_violation_reports_error
test_max_violation_reports_error
test_enum_violation_reports_error
test_bit_width_violation_reports_error
test_multiple_errors_are_collected
```

## Completion checklist

Before finishing, run:

```bash
pytest -q tests/test_schema
pytest -q tests/test_config
pytest -q tests/test_validator
pytest -q
git diff --name-only
git diff --stat
```

If full `pytest -q` fails because other areas are not implemented yet, clearly say so and include focused test results.

Final summary should include:

```text
files changed
APIs implemented
tests run
known limitations
follow-up needed
```