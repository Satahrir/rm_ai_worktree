# Project Progress Snapshot

## Snapshot Date

2026-06-08

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
algorithm exception capture
```

The core is usable when callers construct `TestcaseConfig`, inject packet
inputs, and provide an `Algorithm` implementation.

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

The next active task hardens the existing RM Core Minimal Framework. It should
improve exception lifecycle finalization and stable result serialization
without pulling schema, validation, packing, CLI, or business-algorithm logic
into core.

## Historical Note

Earlier snapshots and journal entries may describe the UVM parser as pending.
Both the Python-output parser and hierarchical JSON output were merged before
this snapshot.
