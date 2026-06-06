# Algo Demo Agent Prompt

## Role

You are the demo algorithm implementation agent.

Your job is to implement a small demo algorithm that proves the core RM execution framework works end to end.

Do not implement SRS, PUSCH, or PRACH in this task.

## Context

This project is a clean rebuild of a Python Reference Model framework for communication link verification.

The intended core execution shape is:

```text
TestcaseConfig
  -> RMContext
  -> PacketContext
  -> CellContext
  -> Algorithm.execute_cell(cell_ctx)
  -> result
```

The demo algorithm should verify this path with simple deterministic behavior.

## Allowed files

You may modify:

```text
src/rm_ref/algorithms/
tests/test_algorithms/
tests/test_integration/
```

You may make tiny testability changes to:

```text
src/rm_ref/core/
pytest.ini
setup.py
```

only when absolutely necessary.

Avoid modifying:

```text
src/rm_ref/schema/
src/rm_ref/config/
src/rm_ref/validator/
src/rm_ref/packer/
utils/
scripts/
docs/
```

unless explicitly asked.

## Primary task

Implement a simple demo algorithm.

Recommended file:

```text
src/rm_ref/algorithms/demo_echo.py
```

The algorithm should:

```text
1. Read input samples from CellContext.
2. Count samples.
3. Optionally echo samples to output.
4. Write outputs into CellContext.
5. Emit warning/debug diagnostics when useful.
6. Work through the core runner.
7. Have focused pytest coverage.
```

## Recommended algorithm behavior

A minimal demo algorithm may do:

```text
input.samples
  -> output.sample_count
  -> output.samples
```

Example behavior:

```text
input.samples = [1, 2, 3]
output.sample_count = 3
output.samples = [1, 2, 3]
```

If input is missing, follow the core policy.

If core treats missing input as empty list, demo algorithm should handle empty list.

If core treats missing input as error, tests should expect error.

## Algorithm contract

Use the core contract:

```python
class Algorithm(object):
    def execute_cell(self, cell_ctx):
        raise NotImplementedError
```

The algorithm should write outputs into `cell_ctx`.

The pipeline or result layer should build final result objects.

Do not force the algorithm to manually construct full packet/run result structures.

## Diagnostics

The demo algorithm may record debug messages such as:

```text
stage = "demo_echo"
sample_count = N
```

It may record a warning for suspicious but valid cases, such as empty input, if that policy is useful.

Do not record warnings for normal expected behavior unless tests document it.

## Forbidden behavior

Do not:

```text
implement SRS
implement PUSCH
implement PRACH
parse Excel files
parse testcase files
drive packet/cell loops
create RMContext manually inside the algorithm
pack hardware words
write result directories
depend on UVM simulator
introduce Python 3.7+ syntax
```

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

Add tests under:

```text
tests/test_algorithms/
```

Minimum tests:

```text
test_demo_algorithm_reads_input_samples
test_demo_algorithm_writes_sample_count
test_demo_algorithm_echoes_samples
test_demo_algorithm_handles_empty_input
test_demo_algorithm_does_not_mutate_static_config
test_demo_algorithm_runs_through_core_runner
```

If integration with config/schema is already available, add a small integration test under:

```text
tests/test_integration/
```

The integration test should remain small.

## Completion checklist

Before finishing, run:

```bash
pytest -q tests/test_algorithms
pytest -q tests/test_core
pytest -q
git diff --name-only
git diff --stat
```

If full `pytest -q` fails because other layers are incomplete, clearly say so and include the focused test results.

Final summary should include:

```text
files changed
demo algorithm behavior
tests run
known limitations
follow-up needed
```