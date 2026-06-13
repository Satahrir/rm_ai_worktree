# Current Implemented Flow

## 1. Purpose

This document describes the flow that is implemented in the repository as of
2026-06-12.

It is the baseline for the next P1 work:

```text
1. add an outer orchestration runner
2. add a minimal cross-layer integration test
3. audit Python 3.6.3 compatibility
```

This document distinguishes current behavior from planned behavior. It does
not describe the missing orchestration runner as already implemented.

## 2. Current Status

### Implemented

The following layers exist as explicit Python APIs:

```text
schema normalization and lookup
UserConfig construction
ConfigResolver
ResolvedConfig
Validator and ValidationResult
ResolvedConfig.to_core_config()
core TestcaseConfig / PacketConfig / CellConfig
RMContext / PacketContext / CellContext
Algorithm.execute_cell(cell_ctx)
packet/cell traversal and lifecycle finalization
diagnostic propagation
RunResult and deterministic to_dict() serialization
```

Each layer has focused tests.

### Limitation

There is no single public API that performs:

```text
resolve -> validate -> convert -> inject payload -> execute
```

The caller must currently connect these APIs manually. Nothing in
`rm_ref.core.run_config()` requires the caller to resolve or validate first.

There is no tracked integration test that crosses all implemented layers.

### Planned P1 Work

P1 should add an outer orchestration boundary and one minimal integration
test. It should not move schema, resolver, validator, payload loading, or
algorithm selection responsibilities into `rm_ref.core`.

## 3. Implemented Flow At A Glance

The complete flow that can be assembled from current APIs is:

```text
schema dict
  |
  v
SchemaDefinition.from_dict()
  |
  +---- optional ----> SchemaRegistry.register()
  |
  v
UserConfig / UserPacketConfig / UserCellConfig
  |
  v
ConfigResolver.resolve()
  |
  v
ResolvedConfig
  |
  v
Validator.validate()
  |
  v
ValidationResult
  |
  +---- errors present ----> caller stops and reports issues
  |
  +---- result.ok ----------> ResolvedConfig.to_core_config()
                                  |
                                  v
                              TestcaseConfig
                                  |
                       caller supplies packet payload
                                  |
                                  v
                         core.run_config(cfg, algorithm)
                                  |
                                  v
                              RunResult
                                  |
                                  v
                          RunResult.to_dict()
```

The arrows between validation, conversion, payload preparation, and execution
are caller-controlled. They are not enforced by one framework entry point.

## 4. Stage 1: Schema Definition

### Owner

```text
src/rm_ref/schema/
```

### Input

The normal input is a plain dictionary containing:

```text
schema_id
word_width
word_count
fields[]
```

Each field may define metadata such as:

```text
name
normalized_name
original_name
scope
word / msb / lsb / width
enum
default
min / max
required
reserved
description
```

### Processing

`SchemaDefinition.from_dict()` delegates to `normalize_schema()`.

Normalization currently:

```text
validates schema identity and word dimensions
normalizes field names
validates word and bit ranges
derives or validates field width
validates enum metadata
validates min/max metadata
assigns global, packet, or cell scope
detects reserved fields
disambiguates duplicate field names when metadata allows it
rejects duplicate normalized names
```

### Output

The output is a `SchemaDefinition`.

It provides:

```python
schema.get_field(name)
schema.require_field(name)
schema.fields_for_scope(scope)
```

`SchemaRegistry` can register and retrieve schemas by `schema_id`. The registry
is explicit and instance-based; there is no hidden global registry.

### Failure Model

Invalid schema structure raises an explicit schema exception. Schema
normalization is setup-time processing, not a normal runtime validation result.

## 5. Stage 2: User Configuration

### Owner

```text
src/rm_ref/config/user_config.py
```

### Data Model

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

`UserConfig.from_dict()` accepts nested dictionaries and constructs the packet
and cell objects.

### Current Meaning

`UserConfig` records what the caller supplied. Values may still contain:

```text
schema field aliases
symbolic enum names
missing values that have schema defaults
omitted packet or cell indexes
```

Constructors deep-copy mapping values so later input mutation does not silently
change the configuration object.

### Limitation

`UserConfig` does not currently describe payload files or packet sample data.
Payload preparation is a separate unresolved boundary.

## 6. Stage 3: Configuration Resolution

### Owner

```text
src/rm_ref/config/resolver.py
```

### Entry Point

```python
resolved = ConfigResolver(registry).resolve(user_config)
```

The caller may instead pass a `SchemaDefinition` directly:

```python
resolved = ConfigResolver().resolve(user_config, schema=schema)
```

### Implemented Behavior

The resolver currently:

```text
selects a schema directly or through SchemaRegistry
checks user schema_id against the selected schema
resolves field aliases to normalized names
checks that each field is used in the correct scope
rejects unknown or ambiguous fields
converts symbolic enum names to numeric values
preserves numeric enum input for later validation
applies schema defaults per scope
assigns omitted packet and cell indexes by position
rejects duplicate packet and cell indexes
records value source as "user" or "schema_default"
preserves packet/cell structure
does not mutate UserConfig
```

### Output Data Model

```text
ResolvedConfig
  case_name
  algorithm_name
  schema_id
  global_values
  global_value_sources
  packets[]

ResolvedPacketConfig
  packet_index
  values
  value_sources
  cells[]

ResolvedCellConfig
  cell_index
  values
  value_sources
```

`ResolvedConfig` is deterministic configuration data. It is not runtime state.

### Failure Model

Resolution failures raise `ConfigResolutionError`. The exception can carry:

```text
schema_id
field_name
bad value
packet_index
cell_index
```

Examples include a missing schema, unknown field, wrong field scope, unknown
enum name, and duplicate index.

## 7. Stage 4: Validation

### Owner

```text
src/rm_ref/validator/
```

### Entry Point

```python
validation = Validator(schema).validate(resolved)
```

### Implemented Checks

Built-in validation currently checks:

```text
unknown resolved fields
required fields
integer type where numeric metadata requires it
minimum and maximum values
enum membership
unsigned bit-width fit
```

Reserved fields are skipped by normal value validation.

Additional callable rules can be registered through `add_rule()`. A custom rule
may add issues directly or return one issue or a list of issues.

### Output

```text
ValidationResult
  errors[]
  warnings[]
  ok
```

Each `ValidationIssue` can carry:

```text
code and severity
message
schema id
normalized and original field names
packet and cell indexes
bad value
expected rule
word and bit metadata
description
custom rule name
```

Normal invalid user values are collected as structured issues instead of
raising immediately.

### Caller Responsibility

The validator does not execute or convert the configuration. The caller must
check:

```python
if not validation.ok:
    # Stop before conversion and execution.
```

This gate is a convention in the current architecture, not an enforced
cross-layer contract.

### Setup Failures

Invalid validator setup, schema mismatch, invalid input type, or unsupported
custom rule output raises `ValidationSetupError`.

## 8. Stage 5: Conversion To Core Config

### Owner

```text
ResolvedConfig.to_core_config()
```

### Implemented Mapping

The conversion creates:

```text
ResolvedConfig       -> TestcaseConfig
global_values        -> GlobalConfig.parameters
ResolvedPacketConfig -> PacketConfig.parameters
ResolvedCellConfig   -> CellConfig.parameters
```

`algorithm_name`, when non-empty, is copied into global core parameters under
the key `algorithm_name`.

Packet and cell indexes are preserved.

### Important Boundary

Conversion prepares static execution configuration only. It does not:

```text
run validation
select or instantiate an Algorithm
load payload
populate PacketConfig.input_pkt_by_cc
run the core pipeline
```

The `algorithm_name` string is metadata. `core.run_config()` still requires an
actual `Algorithm` instance from the caller.

### Payload Gap

`PacketConfig` supports:

```text
input_pkt_by_cc[cell_index] -> cell sample input
```

However, `ResolvedConfig.to_core_config()` currently leaves this mapping empty
because resolved configuration has no payload field. A caller must perform a
separate payload preparation step before execution.

There is no standard payload loader or injection API yet.

## 9. Stage 6: Core Execution

### Owner

```text
src/rm_ref/core/
```

### Public Entry Point

```python
result = run_config(core_config, algorithm)
```

`run_config()` requires:

```text
core_config is TestcaseConfig
algorithm is an Algorithm instance
```

It does not accept `UserConfig` or `ResolvedConfig`.

### Runner Responsibility

The core runner:

```text
checks the two input object types
creates the RMContext
invokes the internal pipeline
captures unexpected algorithm exceptions
builds and returns RunResult
```

### Pipeline Responsibility

The pipeline:

```text
owns packet traversal
owns cell traversal
prepares packet and cell contexts
calls Algorithm.execute_cell(cell_ctx)
records ALGORITHM_EXCEPTION on a failing cell
finalizes every started context
stops traversal after an unexpected exception
```

The pipeline remains fail-fast. It does not execute later cells or packets
after an unexpected algorithm exception.

### Context Preparation

Runtime contexts use these stable scopes:

```text
state
config
derived
input
output
trace
```

Configuration is copied downward:

```text
RMContext.config
  global parameters

PacketContext.config
  global parameters + packet parameters

CellContext.config
  global parameters + packet parameters + cell parameters
```

Payload is exposed to a cell as:

```python
cell_ctx.get_input("samples", [])
```

Algorithm output is normally written through:

```python
cell_ctx.push_output(name, value)
```

### Diagnostic Propagation

Diagnostics recorded on a cell propagate to its packet and run contexts.
Packet diagnostics propagate to the run context.

Errors update status to `ERROR`; warnings update status to `WARNING`.

### Lifecycle State

On success and unexpected algorithm failure:

```text
each started cell has state.completed = True
each started packet has state.completed = True
the run has state.completed = True
packet executed_cell_count matches started cell contexts
run executed_packet_count matches started packet contexts
```

## 10. Stage 7: Results And Serialization

### Result Model

```text
RunResult
  status
  exit_code
  case_name
  algorithm_name
  summary
  packet_outputs[]
  warnings[]
  errors[]
  exception

PacketOutput
  packet_index
  status
  runtime_summary
  cell_outputs[]
  warnings[]
  errors[]

CellOutput
  packet_index
  cell_index
  status
  output
  warnings[]
  errors[]
```

### Exit Behavior

`exit_code` is:

```text
0 when there are no run errors and no unexpected exception
1 when run errors exist or an unexpected exception was captured
```

The runner returns a structured result for an algorithm exception rather than
re-raising it to the caller.

Configuration and setup type errors raised before pipeline execution are not
converted into `RunResult`.

### Stable Serialization

These types implement `to_dict()`:

```text
Diagnostic
CellOutput
PacketOutput
RunResult
```

Serialization:

```text
emits dict/list/scalar values
preserves packet and cell indexes
includes statuses, summaries, diagnostics, and outputs
sorts mapping and set content deterministically
deep-copies mutable values
represents an exception as type and message metadata
rejects unsupported non-plain output values
does not include timestamps or machine-specific data
```

The raw `RunResult.exception` attribute remains available for object API
compatibility, while `RunResult.to_dict()` does not expose the raw exception
object.

## 11. Current Manual Assembly Example

The following example illustrates the currently required caller orchestration.
It is not a single framework API.

```python
from rm_ref.config import ConfigResolver, UserConfig
from rm_ref.core import Algorithm, run_config
from rm_ref.schema import SchemaDefinition
from rm_ref.validator import Validator


class DemoAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        samples = cell_ctx.get_input("samples", [])
        cell_ctx.push_output("sample_count", len(samples))


schema = SchemaDefinition.from_dict(schema_dict)
user_config = UserConfig.from_dict(user_config_dict)

resolved = ConfigResolver().resolve(user_config, schema=schema)
validation = Validator(schema).validate(resolved)

if not validation.ok:
    raise ValueError("configuration validation failed")

core_config = resolved.to_core_config()

# Current payload boundary: the caller must populate input_pkt_by_cc before
# execution. No standard loader or assembly API exists yet.
core_config.packets[0].input_pkt_by_cc[0] = [1, 2, 3]

result = run_config(core_config, DemoAlgorithm())
serialized = result.to_dict()
```

This example exposes the P1 problem: every caller must implement the validation
gate, payload preparation, algorithm construction, and error policy.

## 12. Error Boundaries

The current error model has three distinct categories.

### Setup And Construction Exceptions

Examples:

```text
invalid schema definition
invalid UserConfig structure
missing schema
unknown enum name during resolution
invalid core config object type
invalid Algorithm object type
validator schema mismatch
```

These are raised as exceptions. There is no outer result object that combines
them.

### Validation Issues

Normal invalid resolved values are returned as:

```text
ValidationResult.errors
ValidationResult.warnings
```

The caller decides whether warnings are allowed and must prevent execution when
errors exist.

### Algorithm Execution Diagnostics

Warnings and errors emitted through `CellContext` become core diagnostics and
propagate into `RunResult`.

An unexpected algorithm exception becomes:

```text
ALGORITHM_EXCEPTION diagnostic
RunResult.status = ERROR
RunResult.exit_code = 1
RunResult.exception = raw exception
RunResult.to_dict()["exception"] = stable metadata
```

## 13. Current Test Coverage

### Implemented Focused Coverage

```text
tests/test_schema/
  schema normalization, metadata, duplicate handling, registry behavior

tests/test_config/
  UserConfig construction, defaults, enums, aliases, structure preservation,
  resolution errors, conversion to core config

tests/test_validator/
  required/range/enum/type/bit-width checks, custom rules, immutability

tests/test_core/
  config/context construction, traversal, diagnostics, lifecycle, exceptions,
  result construction, deterministic serialization
```

### Missing Coverage

There is no test that executes:

```text
schema dict
  -> UserConfig
  -> ConfigResolver
  -> ResolvedConfig
  -> Validator
  -> TestcaseConfig
  -> payload injection
  -> core runner
  -> RunResult.to_dict()
```

Because each layer is currently tested separately, cross-layer contract drift
could pass all focused tests.

## 14. P1 Outer Runner Design Boundary

### Planned

P1 should add one outer orchestration API that makes the required order
explicit.

Conceptually:

```text
outer runner
  1. select schema
  2. resolve UserConfig
  3. validate ResolvedConfig
  4. stop on validation errors
  5. convert to TestcaseConfig
  6. inject already-loaded payload through an explicit boundary
  7. obtain an Algorithm instance through explicit injection or a boundary
  8. call core.run_config()
  9. return a structured outer result
```

The outer orchestration package is designed as `rm_ref.runtime`. Expected case
outcomes are represented by the designed `OrchestrationResult`; its
implementation is still planned.

### Required Boundaries

The outer runner must not make `rm_ref.core` depend on:

```text
schema
config resolver
validator
payload file formats
algorithm registries
CLI policy
result directories
```

`core.run_config()` should remain the entry point for an already prepared
`TestcaseConfig` and concrete `Algorithm` instance.

### Validation Gate

The outer runner should make this invariant unavoidable:

```text
core execution is not called when ValidationResult.ok is false
```

The outer result must preserve structured validation issues instead of reducing
them to one string.

### Injection Points

P1 should prefer explicit injected dependencies for:

```text
schema lookup
payload preparation
algorithm construction or selection
```

This keeps file IO, CLI behavior, and business registration outside the
reusable execution core.

## 15. P1 Minimal Integration Test

The first integration test should use one schema, one packet, one cell, and one
small algorithm.

It should verify:

```text
schema defaults are applied
an enum name becomes its numeric value
validation succeeds
packet and cell indexes survive conversion
payload reaches CellContext input.samples
the algorithm writes a CellContext output
RunResult contains that output
RunResult.to_dict() contains only plain values
```

A second test, if included in the same task, should verify:

```text
invalid resolved configuration produces ValidationResult errors
the algorithm is not called
no core context is created
```

The integration test should not use files, network access, FPGA hardware, UVM,
or proprietary tools.

## 16. Python 3.6.3 Compatibility Audit

### Current Constraint

All production and test code must parse and run on Python 3.6.3.

### Planned P1 Audit

The audit should check source and tests for:

```text
dataclasses
typing.Protocol
Literal
TypedDict
built-in generic annotations such as list[str] and dict[str, int]
X | Y union annotations
match/case syntax
f-string debug expressions such as {value=}
standard-library APIs introduced after Python 3.6
```

Simple text search is useful for candidate discovery but is not sufficient for
tokens such as `|`, which can have unrelated meanings. Findings should be
confirmed with syntax-aware inspection or an actual Python 3.6 parser/runtime.

The current development test run under a newer Python interpreter does not by
itself prove Python 3.6.3 compatibility.

## 17. Non-Goals For P1

P1 should not implement:

```text
hardware word packing
payload file format policy
trace/dump/log rendering
result directory creation
CLI exit policy
UVM simulator integration
demo/SRS/PUSCH/PRACH business algorithms
global mutable schema or algorithm registries
```

Those remain separate tasks.

## 18. Known Limitations

The current implemented flow has these limitations:

```text
no unified outer runner
validation can be bypassed by direct core calls
no standard payload loader or payload preparation API
algorithm_name does not select an Algorithm instance
no cross-layer integration test
ValidationIssue and ValidationResult have no stable to_dict() API
setup/resolution/validation/execution outcomes are not unified
no packer integration
no observability renderer
Python 3.6.3 compatibility has not been verified by a dedicated audit
```

These are implementation gaps, not implemented features.

## 19. P1 Design Questions

Detailed question records, decisions, project evidence, ownership, and test
requirements are maintained in:

```text
docs/architecture/14_p1_design_questions.md
```

The current summary is:

```text
1. DECIDED: outer orchestration belongs to rm_ref.runtime, with runtime -> core
   and no reverse dependency from core.
2. DECIDED: OrchestrationResult represents expected setup, validation, and
   execution outcomes without swallowing API misuse or framework bugs. The
   supporting core exception-ownership and lifecycle contract is designed but
   not implemented: a returned RunResult means framework cleanup succeeded,
   while framework and finalizer failures propagate.
3. OPEN: Does the outer runner receive a SchemaDefinition, a SchemaRegistry, or an
   injected schema lookup callable?
4. OPEN: Does it receive an Algorithm instance or an injected algorithm factory?
5. OPEN: What is the minimal payload injection contract before file IO exists?
6. OPEN: P1 requires ValidationIssue and ValidationResult to_dict(); the
   minimum serialized fields and rules remain undecided.
7. OPEN: How will Python 3.6.3 compatibility be verified in CI?
```

### 19.1 Payload Boundary

Status: open question. Previous proposed answers have been withdrawn.

The only implemented facts are:

```text
PacketConfig.input_pkt_by_cc stores packet input by cell index.
The core pipeline exposes the selected value as CellContext input.samples.
ResolvedConfig.to_core_config() does not populate input_pkt_by_cc.
```

P1 still needs to decide:

```text
1. What payload argument, if any, the outer orchestration API accepts.
2. How external payload data maps to packets and cells.
3. Which layer validates missing, extra, or malformed payload entries.
4. Whether P1 only injects already-prepared data or also defines a preparation
   interface.
5. Which payload details remain opaque business data.
```

No `payload_by_packet`, named-input, channel, antenna, or sample-layout format
is currently selected.
