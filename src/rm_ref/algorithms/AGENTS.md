# src/rm_ref/algorithms/AGENTS.md

## Role

`rm_ref.algorithms` contains concrete Reference Model algorithms.

Examples:

```text
demo echo algorithm
SRS algorithm
PUSCH algorithm
PRACH algorithm
```

Algorithms are business/model logic.

They should use the core execution framework but must not redesign it.

## Algorithm contract

Algorithms should follow the core contract:

```python
class Algorithm(object):
    def execute_cell(self, cell_ctx):
        raise NotImplementedError
```

The algorithm receives one `CellContext`.

The algorithm should read prepared input/config from the context and write output back to the context.

## Algorithm responsibilities

Algorithms may:

```text
read cell input data
read resolved or prepared cell parameters
perform model calculation
write intermediate values into context runtime
write final outputs into context runtime
emit warning/error/debug diagnostics through context APIs
```

## Algorithm should not

Algorithms should not:

```text
drive packet loops
drive cell loops
parse Excel files
parse full testcase files
create result directories
decide CLI exit codes
pack hardware interface words unless explicitly part of the algorithm task
silently mutate static config
own global logging setup
depend on UVM simulator runtime
```

## Input location

Algorithms should read from context accessors or stable runtime scopes.

Preferred runtime scopes:

```text
config.*
derived.*
input.*
output.*
trace.*
```

Examples:

```text
config.parameters
input.samples
derived.active_cc_list
output.sample_count
```

Avoid relying on uncontrolled magic string paths when stable accessors or constants exist.

## Output location

Algorithms should write model outputs into context.

Examples:

```text
output.samples
output.sequence
output.k0_list
output.resource_map
output.metrics
```

The pipeline or result layer should build final output objects.

Avoid forcing each algorithm to know the full final result schema.

## Diagnostics

Use context diagnostic APIs when available.

Examples:

```text
cell_ctx.warn(...)
cell_ctx.error(...)
cell_ctx.debug(...)
```

Diagnostics should include useful fields:

```text
packet index
cell index
stage
parameter name
bad value
reason
```

Do not hide serious model errors as debug messages.

## Demo algorithm

The first algorithm should usually be a small demo or echo algorithm.

Its purpose is to verify:

```text
core runner works
packet/cell loop works
input reaches algorithm
algorithm output reaches result
diagnostics propagate correctly
```

Do not start with SRS/PUSCH/PRACH before the demo path is stable.

## Protocol algorithms

Protocol-specific algorithms, such as SRS/PUSCH/PRACH, should keep their own internal modules.

Recommended layout:

```text
algorithms/srs/
  __init__.py
  algorithm.py
  config_keys.py
  sequence.py
  hopping.py
  mapping.py

algorithms/pusch/
  __init__.py
  algorithm.py
  dmrs.py
  mapping.py

algorithms/prach/
  __init__.py
  algorithm.py
  sequence.py
  mapping.py
```

Do not put all protocol code into one huge file.

## Derived values

Be careful when deciding where derived values belong.

Config-level deterministic values may belong in resolved config.

Runtime/model intermediate values should belong in context runtime.

Examples:

```text
ResolvedConfig:
  enum name converted to numeric value
  default applied
  normalized field name

CellContext runtime:
  generated sequence
  resource mapping
  per-slot hopping result
  measured output metric
```

## Payload handling

Algorithms should not directly parse large payload files.

Payload data should be prepared by outer IO or pipeline layers and provided through context.

If an algorithm needs a special payload shape, document it clearly and add tests.

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

Use normal classes and explicit constructors.

## Tests

Tests belong in:

```text
tests/test_algorithms/
```

Minimum expected tests for demo algorithm:

```text
algorithm reads input samples
algorithm writes output sample count
algorithm handles empty input
algorithm records warning when appropriate
algorithm does not mutate static config
algorithm works through core runner
```

Future SRS/PUSCH/PRACH tests should include:

```text
small deterministic examples
boundary parameter values
invalid parameter behavior
known reference vectors when available
resource mapping checks
sequence generation checks
```

## Completion checklist

Before finishing an algorithm task, check:

```text
pytest -q tests/test_algorithms
pytest -q tests/test_core
git diff --name-only
git diff --stat
```

Summarize:

```text
files changed
tests run
known limitations
follow-up needed
```