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
DECIDED
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

Schema construction normally occurs before the orchestrator because the schema
injection contract will receive an existing schema object or provider. A broad
`SchemaError -> SETUP_ERROR` rule is therefore not selected here. Question 3
must define whether any schema lookup failure belongs to the expected setup
classification.

Payload preparation or injection failures are not classified by this decision.
Question 5 must distinguish expected payload data errors from injector
implementation failures.

### Core Exception Ownership Contract

Status:

```text
DECIDED, NOT IMPLEMENTED
```

The current `core.run_config()` catches every `Exception` raised by
`execute_pipeline()`. This can convert lifecycle or framework defects into a
`RunResult`. P1 must not rely on that behavior.

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

### Core Implementation Consequences

The future core-hardening task must:

```text
remove the broad except Exception from core.run_config()
make runner catch only AlgorithmExecutionError
catch Exception only around Algorithm.execute_cell()
propagate FrameworkError from the callback boundary
introduce cleanup-stack lifecycle handling
stop traversal immediately after a finalizer failure
preserve multiple finalizer errors on Python 3.6 without ExceptionGroup
```

These are designed changes. The current implementation still uses broad runner
exception capture and does not implement this lifecycle state machine.

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
serialize `ValidationResult`. The minimum validation serialization contract
remains question 6.

## 4. Question 3: Schema Injection

### Status

```text
OPEN
```

### Question

Does P1 receive a `SchemaDefinition`, a `SchemaRegistry`, an injected lookup
callable, or another schema source?

### Implemented Facts

`ConfigResolver.resolve()` already supports:

```text
an explicit SchemaDefinition
or
a ConfigResolver configured with SchemaRegistry
```

### Evaluation Criteria

The decision should minimize P1 scope while considering:

```text
single-schema use
multi-schema callers
schema lookup failure behavior
test setup complexity
whether schema management policy is being fixed prematurely
```

### Implementation Ownership

The runtime implementation agent owns orchestration use of the selected API.
Changes to schema registry behavior require config/schema-agent scope.

## 5. Question 4: Algorithm Injection

### Status

```text
OPEN
```

### Question

Does P1 receive an `Algorithm` instance, an algorithm factory, a registry, or
another selection mechanism?

### Implemented Facts

`core.run_config()` currently requires a concrete `Algorithm` instance.
`UserConfig.algorithm_name` is metadata and does not select or construct an
algorithm.

### Evaluation Criteria

The decision must clarify:

```text
whether P1 performs algorithm selection
how algorithm construction failures are represented
whether algorithms may carry caller-provided dependencies
whether global registration is avoided
```

### Implementation Ownership

The runtime implementation agent owns injection. A concrete registry or
business selection policy would also require algorithm-agent design and scope.

## 6. Question 5: Payload Boundary

### Status

```text
OPEN
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

No packet/cell mapping format, named-input format, channel format, antenna
format, or sample layout has been selected.

### Evaluation Criteria

The decision must define:

```text
the orchestration API argument
packet and cell mapping
missing and extra entry behavior
the owner of structural validation
whether P1 injects prepared data only
which payload details remain opaque business data
the boundary between rm_ref.runtime and rm_ref.io
```

### Implementation Ownership

Likely future scope:

```text
src/rm_ref/runtime/
tests/test_integration/
```

If file loading or decoding is included, `src/rm_ref/io/` requires a separate
approved scope.

## 7. Question 6: Validation Serialization

### Status

```text
OPEN
```

### Question

What is the minimum stable `to_dict()` contract for `ValidationIssue` and
`ValidationResult` in P1?

### Implemented Facts

Core diagnostics and result objects have deterministic `to_dict()` methods.
Validation result objects currently do not.

### Decided Dependency

P1 requires these methods because the decided `OrchestrationResult.to_dict()`
must serialize validation success and failure without ad hoc inspection of
validator internals.

### Evaluation Criteria

The decision must consider:

```text
whether the outer result requires plain-data serialization
required issue fields
deep-copy behavior for bad values
deterministic ordering
handling of unsupported non-plain values
compatibility with existing core serialization conventions
```

### Implementation Ownership

Serializer changes belong to config/validator-agent scope:

```text
src/rm_ref/validator/
tests/test_validator/
```

Cross-layer behavior belongs in integration tests.

## 8. Question 7: Python 3.6.3 Verification

### Status

```text
OPEN
```

### Question

How will P1 demonstrate Python 3.6.3 compatibility?

### Implemented Facts

The repository requires Python 3.6.3 compatibility. A successful test run on a
newer interpreter does not prove that compatibility.

### Evaluation Criteria

The decision should define:

```text
whether static source checks are added
which incompatible syntax and APIs are checked
whether a real Python 3.6.3 runtime is available
which test subsets run under Python 3.6.3
how CI records the compatibility result
```

Text matching alone is insufficient for ambiguous syntax such as `|` or
version-specific standard-library API usage.

### Implementation Ownership

Potential future scopes include:

```text
scripts/
tests/test_scripts/
CI configuration
tests/test_integration/
```

These paths are outside the current architecture-agent assignment.

## 9. Decision Order

Recommended order:

```text
1. schema injection
2. algorithm injection
3. payload boundary
4. validation serialization details
5. Python 3.6.3 verification
```

Questions 1 and 2 are decided. Questions 3-5 complete the orchestration API.
Question 6 is now required by question 2, but its exact serialized fields and
plain-value rules remain open. Question 7 defines completion evidence and can
be designed in parallel once the P1 source scope is known.
