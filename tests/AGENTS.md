# tests/AGENTS.md

## Test rules

Use pytest.

All tests must support Python 3.6.3.

Tests must not require:

- internet access
- UVM simulator
- FPGA hardware
- proprietary tools
- external services

## Test directories

```text
tests/test_core/
  Core config/context/pipeline/runner tests.

tests/test_schema/
  Schema field and registry tests.

tests/test_config/
  UserConfig, ResolvedConfig, resolver tests.

tests/test_validator/
  Validation rule tests.

tests/test_packer/
  Word packing tests.

tests/test_packet/
  Boundary-neutral packet value and codec tests.

tests/test_algorithms/
  Demo and business algorithm tests.

tests/test_integration/
  End-to-end flow tests.

tests/test_scripts/
  Developer workflow and maintenance script tests.
```

## Preferred style

Use small, explicit tests.

Avoid large fixtures unless they improve readability.

Test error messages, not only exception types.

When testing Python 3.6 compatibility, avoid syntax that cannot run in Python 3.6.

## Test command

Main command:

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
pytest -q tests/test_packet
pytest -q tests/test_algorithms
pytest -q tests/test_integration
```

## Test naming

Use descriptive names.

Good:

```python
def test_resolver_applies_default_value():
    ...
```

Bad:

```python
def test_001():
    ...
```

## Assertion style

Prefer direct assertions.

Good:

```python
assert result.status == "OK"
assert error.field_name == "packet_type"
```

Avoid assertions that hide useful failure information.

## Integration test principle

Integration tests should check the intended flow:

```text
schema dict
  -> user config
  -> resolved config
  -> validation
  -> core TestcaseConfig
  -> runner
  -> result
```

Do not put all behavior into one huge integration test.

Unit tests should catch most failures before integration tests run.
