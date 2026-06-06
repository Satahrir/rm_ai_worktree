# Tests Agent Prompt

## Role

You are the test and integration agent.

Your job is to build a pytest-based safety net for the clean RM rebuild.

You should focus on tests first, not implementation.

## Context

This project is a clean rebuild of a Python Reference Model framework for communication link verification.

The intended flow is:

```text
schema dict
  -> schema registry
  -> user config
  -> resolver
  -> resolved config
  -> validator
  -> optional packer
  -> core config
  -> core runner
  -> result
```

The implementation may not be complete yet.

Your tests should help define and protect expected behavior.

## Allowed files

You may modify:

```text
tests/
pytest.ini
setup.py only if required for test imports
```

You may make tiny testability fixes in `src/` only when absolutely necessary, and you must clearly summarize them.

Avoid large source implementation changes.

## Primary task

Create and maintain the test structure for the project.

The tests should cover:

```text
core execution
schema model
config resolver
validator
packer
demo algorithms
integration flow
Python 3.6 compatibility-sensitive behavior
```

## Test directory layout

Use this structure:

```text
tests/test_core/
tests/test_schema/
tests/test_config/
tests/test_validator/
tests/test_packer/
tests/test_algorithms/
tests/test_integration/
```

Each directory may contain one or more `test_*.py` files.

## Main test command

The main command is:

```bash
pytest -q
```

Focused commands:

```bash
pytest -q tests/test_core
pytest -q tests/test_schema
pytest -q tests/test_config
pytest -q tests/test_validator
pytest -q tests/test_packer
pytest -q tests/test_algorithms
pytest -q tests/test_integration
```

## Test style

Use clear test names.

Good:

```python
def test_resolver_applies_schema_default():
    ...
```

Bad:

```python
def test_001():
    ...
```

Prefer direct assertions.

Good:

```python
assert result.ok is True
assert resolved.get_cell_value(0, 0, "packet_type") == 8
```

Avoid hiding failure details.

## Handling missing implementation

If a module does not exist yet, prefer one of these approaches:

```text
1. Write tests after the corresponding implementation exists.
2. Write a small expectation test and mark it with pytest.skip only with a clear reason.
3. Write integration tests later after core pieces are available.
```

Do not create a large number of permanently skipped tests.

Do not fake implementation inside tests.

## Core tests

Minimum core tests should cover:

```text
config construction
packet/cell normalization
context tree creation
single packet single cell execution
multiple packet execution
algorithm output propagation
diagnostic propagation
runner success result
runner exception result
static config not mutated by runtime output
```

A tiny test algorithm may be used:

```python
class EchoAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        samples = cell_ctx.get_input("samples", [])
        cell_ctx.push_output("sample_count", len(samples))
```

## Schema tests

Minimum schema tests should cover:

```text
schema creation from dict
field width calculation
invalid bit range
enum metadata
default metadata
duplicate original names
registry register/get/has
```

## Config tests

Minimum config tests should cover:

```text
UserConfig construction
packet/cell user values
resolver applies defaults
resolver converts enum names
resolver preserves numeric enum values
resolver rejects unknown enum names
resolver does not mutate user config
resolved config is deterministic
```

## Validator tests

Minimum validator tests should cover:

```text
valid config returns ok
missing required field reports error
min violation
max violation
enum violation
bit width violation
multiple errors collected
warnings do not fail result
validator does not mutate resolved config
```

## Packer tests

Minimum packer tests should cover:

```text
bit width calculation
mask generation
field insertion
field extraction
single field packing
multiple fields same word
multiple words
value too large
negative unsigned value
invalid bit range
overlap detection
reserved field behavior
debug map
```

## Algorithm tests

Start with demo algorithm tests.

Do not start with large SRS/PUSCH/PRACH tests before the demo execution path is stable.

Minimum demo tests:

```text
algorithm reads input samples
algorithm writes output
algorithm handles empty input
algorithm works through core runner
algorithm does not mutate static config
```

## Integration tests

Integration tests should be small.

Target flow:

```text
schema dict
  -> schema registry
  -> UserConfig
  -> Resolver
  -> ResolvedConfig
  -> Validator
  -> core TestcaseConfig
  -> core runner with demo algorithm
  -> RunResult
```

Do not put all behavior into one huge integration test.

## Python 3.6 compatibility

Tests themselves must be Python 3.6-compatible.

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

## Do not

Do not:

```text
rewrite source modules extensively
create fake production APIs only inside tests
depend on internet access
depend on UVM simulator
depend on FPGA hardware
depend on proprietary tools
hide failing tests
leave many permanent skips
```

## Completion checklist

Before finishing, run:

```bash
pytest -q
git diff --name-only
git diff --stat
```

If full tests fail because implementation is incomplete, clearly report:

```text
which tests pass
which tests fail
whether failures are expected because implementation is missing
```

Final summary should include:

```text
files changed
test areas added
tests run
current failures
recommended next implementation task
```