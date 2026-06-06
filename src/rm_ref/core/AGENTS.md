# src/rm_ref/core/AGENTS.md

## Role

`rm_ref.core` owns the stable Reference Model execution framework.

It provides the minimum reusable execution backbone for multiple RM scenarios.

It should not be tied to one concrete protocol, channel, or hardware interface table.

## Core owns

The core package may define:

```text
GlobalConfig
TestcaseConfig
PacketConfig
CellConfig

RMContext
PacketContext
CellContext

Algorithm

Diagnostic
status constants
error classes

packet/cell lifecycle functions
pipeline execution
runner entry point
cell/packet/run result models
```

## Core does not own

The core package must not own:

```text
Excel parsing
JSON testcase parsing
Python testcase discovery
schema extraction
schema registry
business field validation
hardware word packing
SRS/PUSCH/PRACH-specific parameters
result directory creation policy
complex CLI behavior
UVM simulator integration
```

These belong to outer packages or tools.

## Static config model

The core static config model should describe what to execute.

Recommended hierarchy:

```text
TestcaseConfig
  global_cfg
  packets[]

PacketConfig
  packet_index
  parameters
  input_pkt_by_cc
  cells[]

CellConfig
  cell_index
  parameters
```

Static config should not hold runtime outputs.

Static config should not hold execution warnings/errors.

Static config should not hold file handles or streaming readers.

## Runtime context model

The core runtime context model should record what happens during execution.

Recommended hierarchy:

```text
RMContext
  packet_contexts[]

PacketContext
  rm_ctx
  packet_cfg
  cell_contexts[]

CellContext
  rm_ctx
  packet_ctx
  cell_cfg
```

Each context may hold:

```text
runtime state
input data
derived values
output data
warnings
errors
debug logs
trace events
status
```

## Runtime scopes

If using runtime dictionaries, prefer stable scopes:

```text
state.*
config.*
derived.*
input.*
output.*
trace.*
```

Avoid uncontrolled ad-hoc keys in critical paths.

When a key becomes stable, consider defining a constant or accessor method.

## Algorithm contract

The preferred contract is:

```python
class Algorithm(object):
    def execute_cell(self, cell_ctx):
        raise NotImplementedError
```

Algorithm responsibilities:

- read prepared input from `cell_ctx`
- read prepared config from `cell_ctx`
- execute model logic for one cell
- write outputs into `cell_ctx`
- record warnings/errors/debug through context APIs

Algorithm should not:

- drive packet loops
- drive cell loops
- parse Excel
- parse testcase files
- create result directories
- decide CLI exit codes
- modify static config

## Pipeline responsibility

The pipeline owns traversal:

```text
for packet in testcase:
    prepare packet runtime

    for cell in packet:
        prepare cell runtime
        algorithm.execute_cell(cell_ctx)
        build cell output

    finalize packet runtime
    build packet output

build run summary
```

The pipeline should be deterministic and easy to test.

## Result construction

Prefer this direction:

```text
Algorithm writes to CellContext
Pipeline builds CellOutput
Pipeline builds PacketOutput
Runner builds RunResult
```

Avoid forcing every algorithm to know the final result schema.

## Diagnostics

Diagnostics should support:

```text
warning
error
debug
trace
```

Cell-level diagnostics should propagate upward:

```text
CellContext
  -> PacketContext
  -> RMContext
```

Packet-level diagnostics should propagate upward:

```text
PacketContext
  -> RMContext
```

Errors should update status consistently.

## Status model

Use a small, explicit status model.

Typical values:

```text
OK
WARNING
ERROR
SKIPPED
```

Do not rely on ambiguous booleans alone.

## Payload boundary

The core may support injected payload data.

The core should not hard-code payload file formats.

Preferred boundary:

```text
payload_loader(path) -> input_pkt_by_cc
```

The loader itself belongs outside deep core logic.

## Python 3.6 compatibility

Do not use:

- dataclasses
- Protocol
- Literal
- TypedDict
- built-in generic type syntax
- union operator syntax
- match/case

Use normal classes and explicit constructors.

## Tests

Core tests belong in:

```text
tests/test_core/
```

Minimum expected coverage:

```text
config construction
packet/cell normalization
context creation
packet/cell lifecycle
algorithm execution
diagnostic propagation
result construction
runner success path
runner exception path
missing input behavior
```

## Do not

Do not add SRS/PUSCH/PRACH fields to core config classes.

Do not make core depend on generated schema definitions.

Do not make core parse Excel or JSON.

Do not add global mutable registries unless absolutely necessary.

Do not silently change `Algorithm.execute_cell(cell_ctx)` without updating architecture docs and tests.