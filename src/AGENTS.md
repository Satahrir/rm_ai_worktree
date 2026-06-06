# src/AGENTS.md

## Source code rules

All code under `src/` must support Python 3.6.3.

Do not use:

- `dataclasses`
- `typing.Protocol`
- `Literal`
- `TypedDict`
- built-in generic type syntax such as `list[str]`
- `X | Y` union syntax
- `match/case`
- f-string debug syntax such as `{var=}`

Use:

- normal classes
- explicit `__init__`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Union`
- explicit exception classes
- simple functions

## Package boundaries

The main package is:

```text
src/rm_ref/
```

Its intended subpackages are:

```text
core/
schema/
config/
validator/
packer/
io/
observability/
algorithms/
```

Each subpackage owns a separate responsibility.

Do not mix responsibilities across packages.

## Import rules

Prefer stable package imports.

Production modules should not rely on current working directory hacks.

Tests may adjust import path if needed, but library code should not.

Do not introduce circular imports.

When in doubt, move shared constants or small helper functions into a lower-level module.

## Side effect rules

Library code should avoid:

- printing directly
- opening files directly from deep core logic
- reading environment variables directly
- starting subprocesses
- modifying global state

Use explicit boundary modules for:

- IO
- payload loading
- serialization
- trace
- dump
- logging or log rendering

## Core isolation rule

`src/rm_ref/core/` is the stable execution framework.

It must not depend on:

- generated schema definitions
- concrete SRS/PUSCH/PRACH field names
- Excel parsing tools
- external testcase formats
- CLI behavior
- project-specific result directory layout

## Algorithm isolation rule

Algorithms may depend on core contracts.

Algorithms should not own the outer packet/cell loop.

Algorithms should read prepared values from context and write outputs back to context.

## Testing rules

Every public behavior should have pytest coverage.

Use small unit tests first.

Use integration tests only after unit behavior is clear.

Tests must not require:

- internet access
- FPGA hardware
- UVM simulator
- proprietary tools