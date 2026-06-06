# src/rm_ref/config/AGENTS.md

## Role

`rm_ref.config` owns user configuration, resolved configuration, and config resolving behavior.

This package bridges external user input and the stable RM execution core.

The main flow is:

```text
UserConfig
  -> schema defaults
  -> enum conversion
  -> name normalization
  -> derived value preparation
  -> ResolvedConfig
```

The result may later be converted into core execution config:

```text
ResolvedConfig
  -> TestcaseConfig
  -> PacketConfig
  -> CellConfig
```

## Main responsibilities

This package may define:

```text
UserConfig
UserPacketConfig
UserCellConfig

ResolvedConfig
ResolvedPacketConfig
ResolvedCellConfig

ConfigResolver
resolver errors
conversion helpers into core config
```

## UserConfig

`UserConfig` represents what the user wrote.

It may contain:

```text
case name
algorithm name
global settings
packet-level values
cell-level values
raw enum names
missing fields that can be filled by defaults
raw field names from schema
user-friendly aliases
```

`UserConfig` should not contain runtime algorithm state.

## ResolvedConfig

`ResolvedConfig` represents deterministic final values after resolving.

It should contain:

```text
normalized field names
numeric enum values
default values applied
packet/cell structure preserved
schema id references
source metadata when useful
derived values if they are deterministic config-level values
```

Resolved config should be stable enough for:

```text
validation
word packing
conversion into core config
debug dump
reproducible testcase execution
```

## UserConfig vs ResolvedConfig

Keep the distinction clear:

```text
UserConfig:
  What the user provided.

ResolvedConfig:
  What the framework will actually use.
```

Examples:

```text
UserConfig value:
  packet_type = "SRS"

ResolvedConfig value:
  packet_type = 8

UserConfig value:
  missing field with schema default

ResolvedConfig value:
  default applied explicitly
```

## Resolver behavior

The resolver may perform:

```text
schema lookup
field name normalization
alias handling
default value application
enum name-to-value conversion
packet/cell structure normalization
basic type conversion
deterministic derived config calculation
conversion to core TestcaseConfig / PacketConfig / CellConfig
```

Do not hide validation errors by silently fixing invalid values.

## Defaults

Defaults should come from schema metadata or explicit resolver rules.

When applying a default, preserve enough information to explain that the value was defaulted.

Possible metadata:

```text
source = "user"
source = "schema_default"
source = "resolver_default"
```

## Enum handling

Enum fields may allow user input as either:

```text
"SRS"
8
```

Resolver may convert symbolic enum names into numeric values.

Validation should still verify that the final numeric value is legal.

Do not silently accept unknown enum names.

## Derived values

Config-level derived values are allowed when they are deterministic and independent of runtime payload.

Examples:

```text
active cell count
normalized packet index
normalized cell index
symbolic enum numeric value
field aliases resolved
```

Protocol-specific derived values, such as SRS hopping sequence internals, should be placed carefully.

If they are stable configuration derivations, they may belong in resolved config.

If they depend on runtime input or algorithm execution, they belong in context runtime.

## Conversion to core config

The resolver may provide a conversion step:

```text
ResolvedConfig
  -> core.TestcaseConfig
```

This conversion should not run algorithms.

It should only prepare static execution input.

Core config should receive generic packet/cell parameters, not schema-specific classes unless explicitly designed.

## Forbidden responsibilities

`rm_ref.config` must not:

```text
run algorithms
drive packet/cell loops
pack hardware words
write trace files
create result directories
load large payload files directly
mutate RMContext during algorithm execution
silently change static config after execution starts
```

## Dependency rules

Allowed dependencies:

```text
rm_ref.schema
rm_ref.core.config only for conversion into executable config
standard library
typing
```

Avoid depending on:

```text
rm_ref.core.pipeline
rm_ref.core.runner
rm_ref.algorithms
rm_ref.packer implementation details
UVM tools
Excel parser utilities
```

## Error handling

Resolver errors should include:

```text
schema id if available
packet index if available
cell index if available
field name
bad value
reason
```

Examples:

```text
unknown field freqDomainPostion; did you mean freqDomainPosition?
unknown enum name packet_type='SXR'
missing required schema demo1/v1
cannot convert field n_srs='abc' to integer
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
tests/test_config/
```

Minimum expected tests:

```text
construct UserConfig
construct packet/cell user config
apply schema default
convert enum name to value
preserve user-provided numeric enum value
reject unknown enum name
normalize field names
preserve packet/cell structure
produce deterministic ResolvedConfig
convert ResolvedConfig to core TestcaseConfig
do not mutate UserConfig during resolve
```

## Completion checklist

Before finishing a config task, check:

```text
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