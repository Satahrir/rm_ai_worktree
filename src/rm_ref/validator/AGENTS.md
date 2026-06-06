# src/rm_ref/validator/AGENTS.md

## Role

`rm_ref.validator` validates resolved configuration values before execution or packing.

It should catch user configuration errors early and produce clear, structured diagnostics.

The main flow is:

```text
ResolvedConfig
  -> Validator
  -> ValidationResult
```

## Main responsibilities

This package may define:

```text
ValidationErrorInfo
ValidationWarningInfo
ValidationResult
Validator
validation rules
cross-field rule hooks
validator errors
```

## Input

Validator input may include:

```text
ResolvedConfig
schema metadata
business rule callbacks
packet/cell context metadata
```

The validator should work on resolved values, not raw user strings when possible.

## Output

Validator output should be structured.

Recommended shape:

```text
ValidationResult
  ok
  errors[]
  warnings[]
```

A validation result is preferable to raising an exception for normal user configuration mistakes.

Exceptions may still be used for programmer errors, invalid schema objects, or invalid validator setup.

## Required checks

Support at least:

```text
required field
min/max range
enum membership
bit width range
integer type
duplicate field instances
custom cross-field rule hook
```

Future checks may include:

```text
packet-level constraints
cell-level constraints
cross-cell constraints
cross-packet constraints
protocol-specific constraints
```

## Error information

Each validation error should include as much useful context as available:

```text
schema id
field name
original field name
packet index
cell index
bad value
expected rule
word index
msb
lsb
width
description
```

Good error example:

```text
schema demo1/v1 packet 0 cell 1 field c_srs value=99 violates range [0, 63]
```

Bad error example:

```text
invalid value
```

## Warning information

Warnings should be used for suspicious but still executable cases.

Examples:

```text
field is deprecated
value uses default
reserved field ignored
unknown optional field ignored by policy
```

Do not use warnings to hide real errors.

## Validation rule model

Prefer small rule functions or small rule classes.

A rule should be easy to test independently.

Possible simple API:

```python
result = validator.validate(resolved_config, schema)
```

or:

```python
validator.add_rule(rule)
result = validator.validate(resolved_config)
```

Keep the API explicit and Python 3.6-compatible.

## Cross-field rules

Cross-field rules are allowed, but they should be explicit.

Examples:

```text
if pusch_flag == 0, pusch-specific fields must be absent or default
if packet_type == SRS, SRS-required fields must exist
if start_rb + rb_num exceeds bandwidth, report error
```

Cross-field rules should include meaningful names so diagnostics can show which rule failed.

## Mutability rule

Validation should not silently mutate resolved config.

If validation requires normalization, that logic probably belongs in resolver, not validator.

Validator may annotate result objects, but should avoid changing input config.

## Forbidden responsibilities

`rm_ref.validator` must not:

```text
pack hardware words
run algorithms
drive packet/cell loops
parse Excel files
load payload data
create RMContext
write result files
modify static config silently
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
rm_ref.packer implementation details
Excel parser utilities
UVM tools
```

## Relationship with packer

Validator checks semantic correctness.

Packer checks bit placement safety while packing.

For example:

```text
Validator:
  c_srs must be within allowed protocol range.

Packer:
  field value must fit into its declared bit width.
```

Some overlap is acceptable, but responsibility should remain clear.

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
tests/test_validator/
```

Minimum expected tests:

```text
valid config returns ok
missing required field reports error
min violation reports field and expected range
max violation reports field and expected range
enum violation reports allowed values
bit width violation reports word/bit metadata
multiple errors are collected
warnings do not make result fail
cross-field rule hook can report error
validator does not mutate resolved config
```

## Completion checklist

Before finishing a validator task, check:

```text
pytest -q tests/test_validator
pytest -q tests/test_config
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