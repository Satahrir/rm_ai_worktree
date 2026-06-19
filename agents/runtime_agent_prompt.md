# Runtime Agent Prompt

## Role

You are the runtime orchestration implementation agent.

Your job is to implement the first outer orchestration boundary for the clean
Reference Model rebuild:

```text
UserConfig + SchemaDefinition + Algorithm + optional payload mapping
  -> resolve
  -> validate
  -> convert to core config
  -> inject payload
  -> core.run_config()
  -> OrchestrationResult
```

The runtime layer composes existing packages. It must not move schema,
configuration, validation, payload file IO, algorithm selection, or core
execution responsibilities into the wrong layer.

## Context

The current repository already has:

```text
rm_ref.schema.SchemaDefinition
rm_ref.config.UserConfig / ConfigResolver / ResolvedConfig
rm_ref.validator.Validator / ValidationResult
ResolvedConfig.to_core_config()
rm_ref.core.Algorithm / run_config() / RunResult
```

There is not yet a single public API that enforces the order:

```text
resolve -> validate -> convert -> inject payload -> execute
```

This task should add that boundary without changing the deep core.

## Allowed files

You may modify:

```text
src/rm_ref/runtime/
tests/test_integration/
```

You may make tiny package export changes to:

```text
src/rm_ref/__init__.py
```

only if required for a stable import surface.

Avoid modifying:

```text
src/rm_ref/core/
src/rm_ref/schema/
src/rm_ref/config/
src/rm_ref/validator/
src/rm_ref/packer/
src/rm_ref/algorithms/
docs/
utils/
schema_defs/
scripts/
agents/
```

unless explicitly asked.

## Primary task

Implement the P1 runtime runner and outer result model.

Required capabilities:

```text
1. Provide rm_ref.runtime as the outer composition package.
2. Add run_case(user_config, schema, algorithm, payload_by_packet=None).
3. Require an explicit SchemaDefinition.
4. Require an already constructed Algorithm instance.
5. Resolve UserConfig with ConfigResolver and the explicit schema.
6. Validate the resolved config with Validator.
7. Do not call core.run_config() when validation fails.
8. Convert resolved config to core TestcaseConfig only after validation passes.
9. Inject optional payload_by_packet into PacketConfig.input_pkt_by_cc.
10. Return OrchestrationResult for expected setup, validation, and execution outcomes.
```

## Result model

Implement an explicit outer result object:

```text
OrchestrationResult
  status
  validation
  run_result
  exception
```

Use these status values:

```text
PASS
SETUP_ERROR
VALIDATION_ERROR
EXECUTION_ERROR
```

Expected status behavior:

```text
PASS
  validation succeeded, core execution ran, and RunResult.exit_code == 0

SETUP_ERROR
  ConfigResolutionError or PayloadMappingError occurred before core execution

VALIDATION_ERROR
  ValidationResult.ok is false; core execution did not run

EXECUTION_ERROR
  core execution ran and RunResult.exit_code != 0
```

`OrchestrationResult.to_dict()` must emit deterministic plain data suitable
for later JSON/logging boundaries. It should embed `validation.to_dict()` and
`run_result.to_dict()` when those objects are present. Unsupported values
encountered during serialization should propagate rather than being hidden.

## Payload mapping

Runtime accepts optional already prepared in-memory payload:

```python
payload_by_packet = {
    packet_index: {
        cell_index: payload_value,
    },
}
```

Behavior:

```text
payload_by_packet is None
  every cell receives the existing core default []

missing packet or cell entry
  that cell receives []

extra packet index
  PayloadMappingError -> SETUP_ERROR

extra cell index
  PayloadMappingError -> SETUP_ERROR

outer value is not a dict, or packet value is not a dict
  PayloadMappingError -> SETUP_ERROR
```

Runtime validates only mapping shape and packet/cell indexes. Payload values
remain opaque. Runtime must not interpret sample type, shape, channel,
antenna, encoding, or business meaning.

Deep-copy injected values into core config so caller payload mappings are not
mutated through execution. Unexpected copy failures should propagate.

## Error boundary

Do not use broad exception conversion.

Convert only these expected case setup failures into `SETUP_ERROR`:

```text
ConfigResolutionError
PayloadMappingError
```

Propagate these as API misuse or framework failures:

```text
non-UserConfig input
non-SchemaDefinition input
non-Algorithm input
ValidationSetupError
core ConfigError before execution
unexpected runtime/framework exceptions
serialization TypeError from to_dict()
```

The caller owns schema construction, schema lookup, algorithm construction,
file loading, payload decoding, result directories, and CLI exit policy.

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
f-string debug syntax
```

Use normal classes, explicit constructors, and `typing` aliases compatible
with Python 3.6.

## Tests

Add focused integration tests under:

```text
tests/test_integration/
```

Minimum expected tests:

```text
valid schema/user config/payload executes through core
schema defaults and enum conversion are visible to the algorithm
validation errors prevent algorithm execution
schema id mismatch returns SETUP_ERROR
extra packet payload returns SETUP_ERROR
extra cell payload returns SETUP_ERROR
invalid payload mapping shape returns SETUP_ERROR
missing payload entries become []
caller payload is not mutated
algorithm-reported core error becomes EXECUTION_ERROR
algorithm exception captured by core becomes EXECUTION_ERROR
non-SchemaDefinition and non-Algorithm inputs propagate TypeError
OrchestrationResult.to_dict emits plain deterministic data
```

Keep tests small. Use a tiny local test algorithm rather than implementing a
business algorithm.

## Forbidden behavior

Do not:

```text
modify rm_ref.core to depend on runtime/schema/config/validator
select algorithms by name
create global schema or algorithm registries
parse payload files
pack hardware words
write result directories
decide CLI exit codes
hide framework failures as OrchestrationResult statuses
introduce Python 3.7+ syntax
```

## Completion checklist

Before finishing, run:

```bash
pytest -q tests/test_integration
pytest -q tests/test_config
pytest -q tests/test_validator
pytest -q tests/test_core
pytest -q
D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q
python scripts/agent_workflow.py check-scope
git diff --name-only
git diff --stat
```

If the Python 3.6.3 interpreter is unavailable, clearly report that exact
compatibility verification was not completed.

Final summary should include:

```text
files changed
APIs implemented
tests run
known limitations
follow-up needed
```
