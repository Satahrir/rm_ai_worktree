# Core Agent Prompt

## Role

You are the core framework implementation agent.

Your job is to implement the minimal reusable RM execution core for the clean rebuild.

You should focus on `src/rm_ref/core/` and `tests/test_core/`.

## Context

This project is a clean rebuild of a Python Reference Model framework for communication link verification.

The previous architecture document under `docs/reference/` is reference material only.

Use it to understand stable ideas such as:

```text
TestcaseConfig / PacketConfig / CellConfig
RMContext / PacketContext / CellContext
packet/cell lifecycle
Algorithm.execute_cell(cell_ctx)
diagnostic propagation
run result
Python 3.6 compatibility
```

Do not blindly copy old implementation details or old import paths.

## Allowed files

You may modify:

```text
src/rm_ref/core/
src/rm_ref/io/ only if needed for a minimal payload boundary
src/rm_ref/observability/ only if needed for minimal trace/dump boundary
tests/test_core/
```

You may make tiny import/testability changes to:

```text
pytest.ini
setup.py
```

only if required to run tests.

Avoid modifying:

```text
src/rm_ref/schema/
src/rm_ref/config/
src/rm_ref/validator/
src/rm_ref/packer/
src/rm_ref/algorithms/
docs/
utils/
schema_defs/
```

unless explicitly asked.

## Primary task

Implement a minimal executable core framework.

The first version should support:

```text
1. Construct static testcase config.
2. Normalize packet and cell indexes.
3. Build runtime context tree.
4. Execute one Algorithm over packet/cell structure.
5. Allow algorithm to write cell outputs.
6. Collect cell, packet, and run results.
7. Propagate warnings/errors from cell to packet to run.
8. Return a structured run result.
9. Handle algorithm exceptions.
10. Pass focused pytest tests.
```

## Required modules

Implement or refine these modules:

```text
src/rm_ref/core/status.py
src/rm_ref/core/errors.py
src/rm_ref/core/diagnostic.py
src/rm_ref/core/config.py
src/rm_ref/core/context.py
src/rm_ref/core/algorithm.py
src/rm_ref/core/result.py
src/rm_ref/core/lifecycle.py
src/rm_ref/core/pipeline.py
src/rm_ref/core/runner.py
```

Do not create one giant module.

## Required data model

### Static config

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

### Runtime context

Recommended hierarchy:

```text
RMContext
  cfg
  packet_contexts[]

PacketContext
  rm_ctx
  packet_cfg
  cell_contexts[]
  cell_context_by_idx

CellContext
  rm_ctx
  packet_ctx
  cell_cfg
```

## Runtime state

Each context may hold:

```text
runtime
warnings
errors
debug_logs
trace
status
```

Recommended runtime scopes:

```text
state.*
config.*
derived.*
input.*
output.*
trace.*
```

Use helper methods where reasonable.

Examples:

```python
ctx.push_input("samples", samples)
ctx.get_input("samples", default)
ctx.push_output("sample_count", count)
ctx.get_output("sample_count", default)
```

## Algorithm contract

Use this contract:

```python
class Algorithm(object):
    def execute_cell(self, cell_ctx):
        raise NotImplementedError
```

Algorithms should write outputs into `cell_ctx`.

The pipeline should build final result objects.

Do not force every algorithm to build final cell output schema manually.

## Pipeline behavior

Implement deterministic traversal:

```text
for packet:
    prepare packet runtime

    for cell:
        prepare cell runtime
        algorithm.execute_cell(cell_ctx)
        build cell output

    finalize packet runtime
    build packet output

build run result
```

## Minimal lifecycle behavior

Packet preparation may:

```text
copy packet parameters into runtime config scope
copy input_pkt_by_cc into runtime input scope
derive active cell list
derive active cell count
```

Cell preparation may:

```text
copy packet parameters into cell runtime config scope
copy cell parameters into cell runtime config scope
copy cell input samples into input.samples
```

If cell input is missing, choose one explicit policy and test it.

Recommended first policy:

```text
missing input becomes empty list
```

or:

```text
missing input is an error
```

Pick one and document it in tests.

## Diagnostics

Support at least:

```text
warn(code, message, **fields)
error(code, message, **fields)
debug(message, **fields)
```

Diagnostics should include available context:

```text
packet_index
cell_index
code
message
severity
extra fields
```

Cell diagnostics should propagate to packet and run.

Packet diagnostics should propagate to run.

Errors should update status.

## Status values

Use explicit status constants.

Recommended values:

```text
OK
WARNING
ERROR
SKIPPED
```

## Result model

Provide structured result objects or simple classes.

Recommended run result fields:

```text
status
exit_code
case_name
algorithm_name
summary
packet_outputs
warnings
errors
exception
```

Recommended packet output fields:

```text
packet_index
status
warnings
errors
runtime_summary
cell_outputs
```

Recommended cell output fields:

```text
packet_index
cell_index
status
warnings
errors
output
```

Keep result objects easy to inspect in tests.

## Runner behavior

The runner should provide a simple entry point such as:

```python
run_config(cfg, algorithm)
```

or:

```python
run_config(cfg, algorithm_factory_or_registry)
```

For the first version, prefer the simplest testable API.

The runner should catch unexpected exceptions and return a structured error result.

## Python 3.6 compatibility

Do not use:

```text
dataclasses
Protocol
Literal
TypedDict
list[str]
dict[str, int]
X | Y
match/case
```

Use:

```text
normal classes
explicit __init__
typing.Dict
typing.List
typing.Optional
typing.Union
```

## Tests

Add focused tests under:

```text
tests/test_core/
```

Minimum tests:

```text
test_config_constructs_testcase_packet_cell
test_packet_normalize_assigns_indexes
test_context_tree_is_created
test_runner_executes_single_packet_single_cell
test_runner_executes_multiple_packets
test_algorithm_output_is_in_cell_result
test_cell_warning_propagates_to_run
test_cell_error_sets_run_error
test_algorithm_exception_returns_error_result
test_static_config_is_not_mutated_by_runtime_output
```

Use a tiny test algorithm, such as:

```python
class EchoAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        samples = cell_ctx.get_input("samples", [])
        cell_ctx.push_output("sample_count", len(samples))
```

## Forbidden behavior

Do not:

```text
add SRS/PUSCH/PRACH fields to core config classes
make core import generated schemas
make core parse Excel
make core parse JSON testcase files
make core pack hardware words
make core depend on concrete algorithms
create hidden global registries
introduce Python 3.7+ syntax
```

## Completion checklist

Before finishing, run:

```bash
pytest -q tests/test_core
pytest -q
git diff --name-only
git diff --stat
```

If full `pytest -q` fails because other packages are not implemented yet, clearly say so and include the focused test result.

Final summary should include:

```text
files changed
APIs implemented
tests run
known limitations
follow-up needed
```