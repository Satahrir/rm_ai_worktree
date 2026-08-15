# src/rm_ref/AGENTS.md

## Package role

`rm_ref` is the main package of the clean Reference Model rebuild.

It contains the reusable RM framework, input preparation layers, optional packing utilities, and business algorithms.

The package must remain Python 3.6.3 compatible.

## Subpackage layout

```text
rm_ref/core/
  Stable RM execution framework.

rm_ref/schema/
  Schema representation, normalization, and registry.

rm_ref/config/
  UserConfig, ResolvedConfig, and resolver.

rm_ref/validator/
  Validation rules and validation results.

rm_ref/packer/
  Hardware word packing utilities.

rm_ref/packet/
  Boundary-neutral packet values and packet codecs.

rm_ref/io/
  Payload loading and serialization boundaries.

rm_ref/observability/
  Trace, dump, and log rendering helpers.

rm_ref/algorithms/
  Concrete RM algorithms, such as demo, SRS, PUSCH, PRACH.
```

## High-level flow

The intended flow is:

```text
schema definition
  -> schema registry
  -> user config
  -> resolver
  -> resolved config
  -> validator
  -> optional packer
  -> core config
  -> core context
  -> algorithm execution
  -> result / trace / dump
```

Not every step needs to be implemented immediately.

Each step should have a clear owner.

## Dependency direction

Preferred direction:

```text
schema
  -> config
  -> validator
  -> packer

config / validator / packer
  -> core config models only when converting into executable RM config

algorithms
  -> core algorithm/context contracts

io / observability
  -> core data structures where needed
```

Avoid reverse dependencies.

In particular:

- `core` should not import `schema`.
- `core` should not import `config`.
- `core` should not import `validator`.
- `core` should not import `packer`.
- `core` should not import concrete algorithms.
- `core` should not import generated schema definitions.

## Python 3.6 compatibility

Do not use:

- `dataclasses`
- `typing.Protocol`
- `Literal`
- `TypedDict`
- `list[str]`
- `dict[str, int]`
- `tuple[int, int]`
- `X | Y`
- `match/case`

Use:

- normal classes
- explicit `__init__`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Union`

## Public API style

Keep APIs explicit and small.

Prefer objects with named attributes over unclear tuples.

Good:

```python
result.status
result.errors
result.packet_outputs
```

Less preferred:

```python
status, errors, outputs = run(...)
```

## Error handling

Use explicit exception classes for programmer errors and invalid inputs.

Use structured validation result objects for user configuration errors when possible.

Validation and packing errors should include enough context to debug:

- field name
- bad value
- expected rule
- schema id if available
- packet index if available
- cell index if available
- word/bit position if available

## Runtime data rule

Runtime data belongs in context objects.

Static config objects should not store:

- intermediate algorithm state
- trace events
- warnings/errors generated during execution
- output samples
- file handles
- runtime debug logs

## Business field rule

Business-specific protocol fields belong outside the core framework.

Examples:

```text
freq_domain_position
freq_domain_shift
c_srs
b_srs
b_hop
dmrs_type
pusch_flag
prach_format
```

These should be represented through schema/config/resolved config or algorithm-specific modules, not hard-coded into core execution classes.

## Tests

Every subpackage should have focused tests:

```text
tests/test_core/
tests/test_schema/
tests/test_config/
tests/test_validator/
tests/test_packer/
tests/test_packet/
tests/test_algorithms/
tests/test_integration/
```

Do not rely only on integration tests.

## Do not

Do not introduce circular imports.

Do not introduce new runtime dependencies without explicit approval.

Do not change public APIs silently.

Do not mix schema parsing, config resolving, algorithm execution, and result reporting in one module.
