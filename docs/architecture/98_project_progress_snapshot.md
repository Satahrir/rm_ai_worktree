# Project Progress Snapshot

## Snapshot Date

2026-06-14

## Purpose

This document is a maintained project overview, not the authoritative source
for the active assignment.

For live task status, branch, worktree, and scope, read:

```text
<integration-worktree>/agents/project_status.json
docs/architecture/97_current_task.md
```

## Project

The repository is a Python 3.6.3-compatible Reference Model framework rebuild
for FPGA/UVM/SystemVerilog verification environments.

The intended full flow is:

```text
schema / user config
  -> resolved config
  -> validation
  -> optional packing
  -> core config and runtime context
  -> cell algorithm execution
  -> result / trace / dump
```

## Implemented

### RM Core Minimal Framework

The reusable core execution backbone is implemented and covered by focused
tests:

```text
TestcaseConfig / PacketConfig / CellConfig
RMContext / PacketContext / CellContext
Algorithm.execute_cell(cell_ctx)
packet/cell traversal
runtime input/output/config scopes
diagnostic propagation
structured cell/packet/run results
fail-fast algorithm exception capture
exception-safe cell/packet/run lifecycle finalization
deterministic Diagnostic/CellOutput/PacketOutput/RunResult serialization
```

The core is usable when callers construct `TestcaseConfig`, inject packet
inputs, and provide an `Algorithm` implementation.

When an algorithm raises unexpectedly, traversal stops immediately while all
started contexts are finalized and execution counters remain consistent.
Result `to_dict()` methods emit plain deterministic data, represent exceptions
as stable metadata, and deep-copy mutable values.

### Schema, Config, And Validation

Implemented components include:

```text
schema normalization and registry
UserConfig and ResolvedConfig
ConfigResolver
scope defaults and enum-name conversion
structured validation issues
conversion from ResolvedConfig to core TestcaseConfig
```

These components are available as explicit APIs. There is not yet one outer
runner that automatically resolves, validates, converts, and executes.

### UVM Table Utilities

The utility supports:

```text
hierarchical uvm_table_printer text parsing
flat mapped Python para_get output
deterministic hierarchical JSON output
Python 3.6-compatible CLI behavior
atomic generated-file replacement
```

The JSON format preserves source hierarchy. It does not yet map generic JSON
nodes into business-specific `UserConfig` packet/cell semantics.

### Workflow Enforcement

The multi-agent workflow supports:

```text
one branch and worktree per feature agent
integration-worktree authoritative status
branch/worktree/startup-file preflight
task lifecycle gates
scope checks for committed, staged, unstaged, and untracked files
generated current-task documentation
append-only integration journal
```

## Known Limitations

The following areas are not yet complete:

```text
hardware word packer
concrete demo/SRS/PUSCH/PRACH algorithms
payload loading and serialization boundaries
trace/dump/log rendering helpers
end-to-end integration runner
integration tests across schema -> validation -> core execution
package installation metadata
```

The repository should be described as a tested minimal framework and supporting
utilities, not as a complete production RM flow.

## Current Direction

The `core-hardening-v2` task is merged. Core lifecycle finalization and stable
result serialization are implemented without pulling schema, validation,
packing, CLI, or business-algorithm logic into core.

The current implemented schema-to-result flow and P1 orchestration gaps are now
documented in `13_current_implemented_flow.md` and
`14_p1_design_questions.md`.

The outer orchestration package and result model are designed as:

```text
rm_ref.runtime
OrchestrationResult
```

The remaining P1 boundaries are also decided:

```text
caller injects one explicit SchemaDefinition
caller injects one already constructed Algorithm instance
runtime accepts optional payload_by_packet[packet_index][cell_index]
missing payload entries use []
extra payload indexes and malformed mappings are setup errors
ValidationIssue and ValidationResult require stable plain-data to_dict()
```

These contracts are designed but not implemented.

The supporting core exception-ownership contract is implemented. Core now:

```text
catches algorithm-owned callback failures at the plugin boundary
propagates explicit framework failures
uses cleanup lifecycle states to prevent duplicate finalization
stops business traversal after finalizer failure
attempts required outer cleanup
preserves the primary error and all finalizer failures
returns RunResult only when framework cleanup succeeds
```

The repository has also been exercised with the exact local interpreter:

```text
D:\ProgramData\miniconda3\envs\py3p6\python.exe
Python 3.6.3
pytest 6.2.4
133 passed
```

Pytest 6.2.4 warned that it does not recognize the current `pytest.ini`
`pythonpath` option. A static compatibility checker and explicit compatible
import-path setup remain implementation work.

The next implementation order is validation serialization, runtime and
`OrchestrationResult`, payload mapping with cross-layer tests, then the static
Python 3.6 compatibility gate.

## Historical Note

Earlier snapshots and journal entries may describe the UVM parser as pending.
Both the Python-output parser and hierarchical JSON output were merged before
this snapshot.
