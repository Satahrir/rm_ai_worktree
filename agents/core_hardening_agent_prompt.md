# Core Hardening Agent Prompt

## Role

You are the RM core hardening agent.

The RM Core Minimal Framework is already implemented and usable. Improve its
reliability without expanding core into schema, validation, packing, file
parsing, CLI, or business-algorithm ownership.

Before implementation, run:

```powershell
python scripts/agent_workflow.py preflight
```

Stop if preflight reports any error.

## Goal

Harden two existing core contracts:

```text
1. deterministic lifecycle finalization when an algorithm raises
2. stable dictionary serialization for diagnostics and run results
```

Do not redesign `Algorithm.execute_cell(cell_ctx)`.

## Required Behavior

### Exception Lifecycle

The runner remains fail-fast: an unexpected algorithm exception stops further
packet/cell traversal and returns a structured error result.

For contexts started before the exception:

```text
the active cell is finalized
the active packet is finalized
the run is finalized
completed and executed counters remain internally consistent
the ALGORITHM_EXCEPTION diagnostic remains attached to the failing cell,
packet, and run
```

Do not execute later packets or cells after an unexpected exception.

### Result Serialization

Add explicit deterministic `to_dict()` methods for:

```text
Diagnostic
CellOutput
PacketOutput
RunResult
```

The serialized structure must:

```text
contain plain dict/list/scalar values
preserve packet and cell indexes
include status, warnings, errors, summaries, and outputs
represent an exception as stable metadata, not a raw exception object
deep-copy mutable values so serialized mutation cannot alter result objects
avoid timestamps and machine-specific data
```

Keep existing object attributes and execution behavior compatible.

## Allowed Scope

Modify only:

```text
src/rm_ref/core/
tests/test_core/
```

Do not modify:

```text
src/rm_ref/schema/
src/rm_ref/config/
src/rm_ref/validator/
src/rm_ref/packer/
src/rm_ref/algorithms/
utils/
schema_defs/
docs/
```

## Tests

Add focused coverage for:

```text
successful run lifecycle finalization
failing cell, packet, and run finalized state
fail-fast traversal after an exception
Diagnostic.to_dict()
CellOutput.to_dict()
PacketOutput.to_dict()
RunResult.to_dict() on success
RunResult.to_dict() exception metadata
serialized mutation does not mutate result objects
```

Keep tests Python 3.6-compatible.

## Non-Goals

Do not implement:

```text
schema resolution or validation orchestration
payload file loading
hardware packing
JSON testcase parsing
CLI behavior
result-directory policy
concrete RM algorithms
package installation metadata
```

## Completion

Run:

```powershell
python -m pytest -q tests/test_core
python -m pytest -q
python scripts/agent_workflow.py check-scope
git status --short
```

Report files changed, API behavior, tests, failures, limitations, and
follow-up. Do not update shared workflow status or journal files. Do not
commit unless explicitly requested.
