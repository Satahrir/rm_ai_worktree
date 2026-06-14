# P1 Design Questions

## 1. Purpose

This document records the design questions that must be resolved before P1
orchestration implementation.

It is organized for handoff to future agents. Each question records:

```text
status
question
implemented facts
decision or evaluation criteria
architecture consequences
implementation ownership
required tests
```

Statuses are:

```text
OPEN
DECIDED
IMPLEMENTED
```

A decision is not implemented behavior until matching source code and tests
exist.

## 2. Question 1: Orchestration Package

### Status

```text
IMPLEMENTED
```

### Question

Which package owns outer orchestration without confusing it with
`rm_ref.core.runner` or reversing the core dependency direction?

### Implemented Facts

The current core entry point is:

```python
run_config(core_config, algorithm)
```

It requires an already prepared `TestcaseConfig` and a concrete `Algorithm`
instance.

Current dependency facts include:

```text
ResolvedConfig.to_core_config()
  config -> core config models

Validator
  validator -> schema + config

core.run_config()
  core-only execution dependencies
```

`rm_ref.core` does not currently import schema, config, validator, generated
schema definitions, payload loaders, or CLI modules.

### Decision

Outer orchestration belongs to:

```text
rm_ref.runtime
```

The dependency direction is:

```text
rm_ref.runtime
  -> rm_ref.schema
  -> rm_ref.config
  -> rm_ref.validator
  -> rm_ref.core
```

The diagram means runtime is the composition layer and may call the required
outer preparation APIs plus core execution. It does not mean schema imports
config or that config imports validator.

The mandatory boundary is:

```text
runtime -> core
core -X-> runtime
core -X-> schema
core -X-> config
core -X-> validator
core -X-> payload or CLI policy
```

`rm_ref.core` continues to own execution of prepared core configuration only.

### Consequences

`rm_ref.runtime` may coordinate:

```text
configuration resolution
validation
conversion to TestcaseConfig
payload preparation or injection through the contract selected in question 5
delegation to core.run_config()
outer result construction
```

It must not automatically own:

```text
CLI argument parsing
CLI exit policy
result directory creation
specific payload file formats
business algorithm selection policy
global mutable registries
```

Those responsibilities require explicit boundary decisions.

### Implementation Ownership

Implementation requires a future task whose allowed scope includes:

```text
src/rm_ref/runtime/
tests/test_integration/
```

Other paths may be required depending on decisions 2-7. The architecture agent
must not implement this package under the current documentation-only task.

### Required Tests

At minimum:

```text
runtime can execute a valid resolved and validated configuration through core
validation errors prevent core execution
core imports remain independent of runtime/schema/config/validator
```

## 3. Question 2: Outer Result Model

### Status

```text
DECIDED
```

### Question

What structured result represents setup or resolution failure, validation
failure, core execution success, and core execution error?

### Implemented Facts

```text
resolution and setup failures currently raise exceptions
normal validation failures produce ValidationResult
core execution produces RunResult
algorithm exceptions are captured in RunResult
```

There is no existing result object that combines all four outcomes.

### Decision

The orchestrator returns one `OrchestrationResult` for expected outcomes of one
case execution.

The outer status values are:

```text
PASS
SETUP_ERROR
VALIDATION_ERROR
EXECUTION_ERROR
```

Their meanings are:

```text
PASS
  Resolution and validation succeeded, core execution ran, and
  RunResult.exit_code == 0. Core warnings do not by themselves make this an
  execution error.

SETUP_ERROR
  A specifically classified, expected case-setup failure occurred before core
  execution. For the current API, ConfigResolutionError is the known example.

VALIDATION_ERROR
  ValidationResult.ok is false. Core execution must not run.

EXECUTION_ERROR
  Core execution ran and RunResult.exit_code != 0. This includes an algorithm
  exception already captured by core.run_config().
```

The minimum object contract is:

```text
OrchestrationResult
  status
  validation
  run_result
  exception
```

Attribute presence is:

```text
PASS
  validation = successful ValidationResult
  run_result = RunResult
  exception = None

SETUP_ERROR
  validation = None
  run_result = None
  exception = expected setup exception

VALIDATION_ERROR
  validation = failed ValidationResult
  run_result = None
  exception = None

EXECUTION_ERROR
  validation = successful ValidationResult
  run_result = failed RunResult
  exception = RunResult.exception, which may be None when failure was reported
              through diagnostics rather than an unexpected algorithm
              exception
```

`OrchestrationResult` must provide deterministic `to_dict()` output for later
JSON, logging, and UVM boundaries.

### Exception Boundary

The orchestrator must not use a broad `except Exception` to convert every
failure into `SETUP_ERROR`.

Expected case failures may be wrapped only through an explicit exception
classification. Based on the current implementation:

```text
ConfigResolutionError
  expected resolution failure -> SETUP_ERROR

TypeError caused by invalid API object types
  propagate

ValidationSetupError
  propagate

core ConfigError raised before execution because the prepared core contract is
invalid
  propagate

unsupported non-plain values encountered by to_dict()
  propagate

unexpected runtime or framework exception
  propagate
```

Schema construction and lookup occur before the orchestrator because P1
receives an explicit `SchemaDefinition`. A broad
`SchemaError -> SETUP_ERROR` rule is therefore not selected.

The decided payload boundary classifies invalid mapping shape and unknown
packet/cell indexes as `PayloadMappingError -> SETUP_ERROR`. Unexpected
exceptions raised by payload values or copying still propagate.

### Core Exception Ownership Contract

Status:

```text
IMPLEMENTED
```

Before `core-exception-ownership-v1`, `core.run_config()` caught every
`Exception` raised by `execute_pipeline()`. The implemented runner now catches
only `AlgorithmExecutionError`; framework, lifecycle, result-building, and
serialization failures propagate.

The designed boundary is:

```text
run_config() returns RunResult
  -> core execution and lifecycle cleanup completed without framework failure
  -> runtime maps exit_code != 0 to EXECUTION_ERROR

run_config() raises
  -> API misuse, setup failure, framework failure, lifecycle failure, or
     result-building failure
  -> runtime does not convert it to EXECUTION_ERROR
```

Core status remains:

```text
OK
WARNING
ERROR
SKIPPED
```

`EXECUTION_ERROR` belongs only to `OrchestrationResult`. A future optional
`RunResult.failure_kind` may distinguish:

```text
REPORTED_ERROR
  The algorithm recorded an error diagnostic and returned normally.

ALGORITHM_EXCEPTION
  A non-framework exception escaped Algorithm.execute_cell().
```

Runtime classification must use `RunResult.exit_code`, not exception class or
the presence of a raw exception object.

### Callback Trust Boundary

`Algorithm.execute_cell(cell_ctx)` is a plugin trust boundary.

```text
FrameworkError escaping the callback
  framework-owned; propagate

any other Exception escaping the callback
  algorithm-owned; wrap as AlgorithmExecutionError

BaseException such as KeyboardInterrupt or SystemExit
  do not catch
```

This classification has an explicit limitation. Python cannot reliably infer
whether a bare `KeyError`, `AttributeError`, or similar exception inside the
callback stack originated in algorithm code or in a framework API defect. If a
framework defect crosses this boundary without being explicitly marked as
`FrameworkError`, P1 will classify it as an algorithm failure.

Core APIs must therefore use explicit exception ownership:

```text
FrameworkError
  framework implementation or lifecycle failure

AlgorithmContextUsageError
  algorithm misuse of a context API; algorithm-owned

AlgorithmExecutionError
  internal wrapper used to carry an algorithm-owned callback failure
```

P1 must not use traceback paths, exception messages, or ordinary Python
exception classes to guess ownership.

### Lifecycle Contract

The pipeline remains fail-fast:

```text
1. Any prepare, algorithm, diagnostic-recording, or finalize failure stops
   further business traversal.
2. The pipeline still attempts required outer cleanup for every active context.
3. Cleanup records all finalizer failures without retrying a failed finalizer.
4. Any finalizer failure prevents RunResult creation.
5. LifecycleFinalizationError becomes the top-level exception and preserves
   the primary error plus all finalizer errors.
```

The minimum lifecycle states are:

```text
NEW
ACTIVE
FINALIZING
FINALIZED
FINALIZE_FAILED
```

The minimum transition rules are:

```text
NEW -> ACTIVE
  Context is registered on the cleanup stack before risky initialization.

ACTIVE -> FINALIZING -> FINALIZED
  Normal one-time cleanup.

ACTIVE -> FINALIZING -> FINALIZE_FAILED
  Cleanup failed; record the error and never retry that context.
```

P1 keeps the existing public `prepare_run()`, `prepare_packet()`, and
`prepare_cell()` entry points. Their internal order must become:

```text
create context
register context
push cleanup item and mark ACTIVE
perform risky initialization
return context
```

This lets cleanup find a context when preparation fails after activation.
Public create/register/prepare APIs are not required for P1.

### Exception Priority

The designed priority is:

```text
1. LifecycleFinalizationError
2. DiagnosticRecordingError
3. FrameworkError, prepare failure, or unexpected framework exception
4. AlgorithmExecutionError
5. No exception; build RunResult from diagnostics
```

Required preservation rules are:

```text
algorithm exception only
  runner catches AlgorithmExecutionError and returns RunResult(ERROR)

algorithm exception plus diagnostic-recording failure
  propagate DiagnosticRecordingError
  preserve the original algorithm exception and recording exception

any primary failure plus one or more finalizer failures
  propagate LifecycleFinalizationError
  preserve the primary failure and every finalizer failure

reported algorithm error plus finalizer failure
  propagate LifecycleFinalizationError; do not return RunResult
```

`RunResult.exception`, if retained, may contain only the original algorithm
exception. It must never contain a framework or lifecycle exception.
Serialization must emit stable exception metadata rather than a raw exception
object.

### Implemented Core Behavior

The merged core implementation:

```text
remove the broad except Exception from core.run_config()
make runner catch only AlgorithmExecutionError
catch Exception only around Algorithm.execute_cell()
propagate FrameworkError from the callback boundary
introduce cleanup-stack lifecycle handling
stop traversal immediately after a finalizer failure
preserve multiple finalizer errors on Python 3.6 without ExceptionGroup
```

This behavior was implemented by feature commit `6b9b2cc` and merged into
`main` as `4dfdab1`.

The reviewed design input is archived at:

```text
docs/architecture/archive/p1_question2_exception_ownership_answer.txt
```

### Core Fault-Injection Tests

Required tests include:

```text
reported error -> RunResult(ERROR), no exception
algorithm exception -> RunResult(ERROR), original exception preserved
FrameworkError from callback -> propagate
bare callback KeyError -> algorithm failure under the documented trust boundary
prepare failure -> propagate after cleanup
cell finalizer failure -> stop later cells and clean packet/run
packet finalizer failure -> stop later packets and clean run
multiple finalizer failures -> preserve every failure
algorithm exception plus finalizer failure -> LifecycleFinalizationError
diagnostic-recording failure -> DiagnosticRecordingError
diagnostic-recording plus finalizer failure -> LifecycleFinalizationError
result construction and serialization failures -> propagate
```

### API Boundary

This decision defines result behavior, not the final `run()` signature.
Schema, algorithm, and payload parameters remain governed by questions 3-5.

### Implementation Ownership

Likely future scope:

```text
src/rm_ref/runtime/
tests/test_integration/
```

Validator scope is required because `OrchestrationResult.to_dict()` must
serialize `ValidationResult`. Question 6 defines the required serialization
contract.

## 4. Question 3: Schema Injection

### Status

```text
DECIDED
```

### Question

Does P1 receive a `SchemaDefinition`, a `SchemaRegistry`, an injected lookup
callable, or another schema source?

### Implemented Facts

`ConfigResolver.resolve()` already supports an explicit `SchemaDefinition` or
a resolver configured with `SchemaRegistry`.

### Decision

P1 receives one already constructed `SchemaDefinition` for each case:

```python
run_case(user_config, schema, algorithm, payload_by_packet=None)
```

The caller owns schema loading, construction, registry lookup, and selection.
Runtime validates the explicit object and resolves with:

```python
ConfigResolver().resolve(user_config, schema=schema)
```

Multi-schema callers may use a registry outside runtime:

```python
schema = registry.get(user_config.schema_id)
result = run_case(user_config, schema, algorithm, payload_by_packet)
```

P1 does not accept a registry or schema-provider callback. This keeps schema
management policy outside reusable orchestration.

### Error Boundary

```text
schema is not SchemaDefinition
  API misuse; propagate TypeError

schema construction failed before run_case()
  outside runtime; propagate the schema exception

UserConfig.schema_id does not match the explicit schema
  ConfigResolutionError -> SETUP_ERROR
```

Runtime must not broadly convert every `SchemaError` to `SETUP_ERROR`.

### Implementation Ownership

The runtime implementation agent owns explicit schema injection. No schema
registry change is required for P1.

### Required Tests

```text
explicit SchemaDefinition resolves matching UserConfig
schema-id mismatch returns SETUP_ERROR with ConfigResolutionError
non-SchemaDefinition input propagates as API misuse
runtime does not require or construct SchemaRegistry
```

## 5. Question 4: Algorithm Injection

### Status

```text
DECIDED
```

### Question

Does P1 receive an `Algorithm` instance, an algorithm factory, a registry, or
another selection mechanism?

### Implemented Facts

`core.run_config()` currently requires a concrete `Algorithm` instance.
`UserConfig.algorithm_name` is metadata and does not select or construct an
algorithm.

### Decision

P1 receives one already constructed `Algorithm` instance:

```python
run_case(user_config, schema, algorithm, payload_by_packet=None)
```

The caller owns algorithm selection, construction, dependency injection, and
whether an instance is reused across cases. Runtime passes the same instance
to `core.run_config()` and does not implement a factory, registry, or global
selection policy.

Runtime guarantees one instance is used within one `run_case()` call. It does
not isolate state when the caller deliberately reuses an instance across
calls. Callers should normally construct a new instance per case.

### Algorithm Names

```text
UserConfig.algorithm_name
  caller-provided business/configuration metadata

RunResult.algorithm_name
  actual Python algorithm class name used by core
```

P1 does not require these values to match. Stable business-name-to-class
binding belongs to a future algorithm registry design.

### Error Boundary

```text
algorithm is not an Algorithm instance
  API misuse; runtime raises TypeError

algorithm construction fails
  outside runtime; propagate to the caller

Algorithm.execute_cell() fails
  use the implemented core callback ownership contract
```

### Implementation Ownership

The runtime implementation agent owns explicit instance injection. No
algorithm package or registry change is required for P1.

### Required Tests

```text
runtime passes the exact injected Algorithm instance to core
algorithm state remains visible on the injected instance
non-Algorithm input propagates as API misuse
runtime does not select by UserConfig.algorithm_name
```

## 6. Question 5: Payload Boundary

### Status

```text
DECIDED
```

### Question

What is the minimum payload contract between external preparation and outer
orchestration?

### Implemented Facts

```text
PacketConfig.input_pkt_by_cc stores input values by cell index
ResolvedConfig.to_core_config() leaves input_pkt_by_cc empty
the core pipeline exposes the selected value as CellContext input.samples
there is no standard payload loader or injection API
```

### Decision

P1 accepts optional, already prepared in-memory payload through:

```python
payload_by_packet = {
    packet_index: {
        cell_index: payload_value,
    },
}
```

The orchestration signature is:

```python
run_case(user_config, schema, algorithm, payload_by_packet=None)
```

Runtime validates only mapping structure and packet/cell indexes, then copies
values into `PacketConfig.input_pkt_by_cc`. Payload values remain opaque.
Runtime does not validate sample element types, shape, channel, antenna,
encoding, or business meaning.

### Missing And Extra Entries

```text
payload_by_packet is None
  every cell receives the existing core default []

packet or cell entry is absent
  that cell receives []

packet index does not exist in the resolved core config
  PayloadMappingError -> SETUP_ERROR

cell index does not exist in the referenced packet
  PayloadMappingError -> SETUP_ERROR

outer value is not a dict, or a packet value is not a dict
  PayloadMappingError -> SETUP_ERROR
```

Missing payload is not inherently invalid because some algorithms use only
configuration. Algorithms own business validation of empty or malformed
payload values.

### Ownership And Copying

Runtime deep-copies injected values into core configuration and does not mutate
the caller's mapping. Core continues to isolate context input during context
preparation.

Unexpected exceptions raised by payload objects during copying propagate.
They are not silently converted into `SETUP_ERROR`.

### Runtime And IO Boundary

```text
caller or rm_ref.io
  file loading, decoding, format conversion, and mapping construction

rm_ref.runtime
  packet/cell index validation and injection

algorithm
  payload shape and business-semantic validation

rm_ref.core
  expose the injected value as CellContext input.samples
```

P1 does not define payload file formats or implement file IO.

### Implementation Ownership

Likely future scope:

```text
src/rm_ref/runtime/
tests/test_integration/
```

`PayloadMappingError` belongs to runtime. File loading or decoding remains a
separate `rm_ref.io` task.

### Required Tests

```text
payload reaches the matching packet and cell
missing mapping entries produce []
extra packet index returns SETUP_ERROR
extra cell index returns SETUP_ERROR
invalid mapping shape returns SETUP_ERROR
caller payload is not mutated
payload content is not interpreted by runtime
```

## 7. Question 6: Validation Serialization

### Status

```text
DECIDED
```

### Question

What is the minimum stable `to_dict()` contract for `ValidationIssue` and
`ValidationResult` in P1?

### Implemented Facts

Core diagnostics and result objects have deterministic `to_dict()` methods.
Validation issues and results now implement the decided serialization contract.

### Decision

`ValidationIssue.to_dict()` always emits this fixed field set, including
fields whose value is `None`:

```text
severity
code
message
schema_id
field_name
original_field_name
packet_index
cell_index
value
expected_rule
word
msb
lsb
width
description
rule_name
```

`ValidationResult.to_dict()` emits:

```python
{
    "ok": result.ok,
    "errors": [issue.to_dict() for issue in result.errors],
    "warnings": [issue.to_dict() for issue in result.warnings],
}
```

Issue order remains discovery order. Dictionary iteration order is not part of
the API contract.

### Plain-Value Rules

The serializer creates independent plain data using rules equivalent to core
result serialization:

```text
None, bool, int, float, str
dict with scalar keys
list
tuple -> list
set/frozenset -> deterministically sorted list
```

Unsupported values or dictionary keys raise `TypeError`. The serializer must
not hide unsupported objects by calling `str()` or `repr()`.

Validator must not import the serializer from `rm_ref.core`. P1 keeps a small
validator-local helper unless a lower-level serialization package is designed
separately.

`to_dict()` output must not share mutable containers with issue values. This
decision does not change `ValidationIssue.__init__()` ownership behavior.

Serialization failure propagates. It is not converted to `SETUP_ERROR` or
`VALIDATION_ERROR`.

### Implemented Behavior

The merged validator implementation:

```text
emits every fixed ValidationIssue field, including None values
emits ValidationResult ok/errors/warnings
preserves issue discovery order
creates independent plain containers
rejects scalar and container subclasses
sorts sets deterministically, including floats by IEEE-754 bytes
raises fixed-message TypeError without inspecting unsupported objects
does not import serialization helpers from rm_ref.core
```

Circular containers are not supported and may fail through recursion. They
remain outside the current plain-data contract.

The implementation was committed on `codex/config` through `e790162`,
`e8a539b`, and `ded8d75`, then merged into `main` as `2d83da4`.

### Implementation Ownership

Serializer changes belong to config/validator-agent scope:

```text
src/rm_ref/validator/
tests/test_validator/
```

Cross-layer behavior belongs in integration tests.

### Required Tests

```text
successful result serializes to ok=True with empty lists
all ValidationIssue fields are present
errors and warnings retain discovery order
tuple and set values become deterministic plain lists
mutating serialized output does not mutate the issue
unsupported value and key types raise TypeError
OrchestrationResult embeds validation.to_dict() (future runtime integration)
```

## 8. Question 7: Python 3.6.3 Verification

### Status

```text
DECIDED
```

### Question

How will P1 demonstrate Python 3.6.3 compatibility?

### Implemented Facts

The repository requires Python 3.6.3 compatibility. A successful test run on a
newer interpreter does not prove that compatibility.

The local exact-version interpreter is:

```powershell
D:\ProgramData\miniconda3\envs\py3p6\python.exe
```

### Decision

P1 uses both a real local Python 3.6.3 test run and a future static
compatibility check.

The required runtime verification command is:

```powershell
D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q
```

P1 must also run the full suite on the normal modern development interpreter.

On June 14, 2026, the existing repository baseline produced:

```text
Python 3.6.3 :: Anaconda, Inc.
pytest 6.2.4
133 passed
```

The run emitted one warning because pytest 6.2.4 did not recognize the current
`pytest.ini` `pythonpath` option. Tests passed, but import-path setup must be
made explicit rather than relying on environment-specific path state.

### Static Compatibility Check

A future script should use AST/token-aware checks for prohibited syntax and
known post-3.6 APIs. Text search alone is insufficient for ambiguous syntax.
At minimum it should check:

```text
dataclasses
typing.Protocol, Literal, and TypedDict
built-in generic annotations
X | Y type unions
match/case
f-string debug expressions
known standard-library APIs or keyword arguments added after Python 3.6
```

The script is an early gate, not a substitute for the real interpreter run.

### Completion Evidence

Compatibility may be reported as verified only when:

```text
the exact interpreter reports Python 3.6.3
the required P1/full test scope passes under that interpreter
the modern-Python suite passes
the static compatibility check passes once implemented
```

If the 3.6.3 run is unavailable, documentation must say compatibility is
unverified.

### Implementation Ownership

Potential future scopes include:

```text
scripts/
tests/test_scripts/
pytest import-path configuration
CI configuration
tests/test_integration/
```

These paths are outside the current architecture-agent assignment.

### Required Tests

```text
full suite under the exact Python 3.6.3 interpreter
full suite under the modern development interpreter
focused tests for every static-check violation category
test import setup that does not depend on an unrecognized pytest.ini option
```

## 9. Decision Order

Questions 1-7 are decided. The next implementation order is:

```text
1. ValidationIssue and ValidationResult serialization
2. rm_ref.runtime and OrchestrationResult
3. payload mapping and cross-layer integration tests
4. static Python 3.6 compatibility check and import-path cleanup
```

These decisions define implementation contracts. They do not mean runtime,
payload mapping, validation serialization, or the static compatibility check
already exists.
