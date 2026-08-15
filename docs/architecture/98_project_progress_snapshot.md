# Project Progress Snapshot

## Snapshot Date

2026-06-25

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
stable ValidationIssue and ValidationResult serialization
conversion from ResolvedConfig to core TestcaseConfig
runtime run_case() outer orchestration
OrchestrationResult
payload_by_packet in-memory injection
cross-layer integration tests
```

These components are available as explicit APIs. `rm_ref.runtime.run_case()`
now enforces the normal order:

```text
resolve -> validate -> convert -> inject payload -> execute
```

### UVM Table Utilities

The utility supports:

```text
hierarchical uvm_table_printer text parsing
flat mapped Python para_get output
deterministic hierarchical JSON output
schema adapter from parsed UVM table JSON/text to RM SchemaDefinition dict
deterministic demo2 schema and adapter report generation
Python 3.6-compatible CLI behavior
atomic generated-file replacement
```

The JSON format preserves source hierarchy. The schema adapter maps demo2 table
fields into stable cell-scope schema field names accepted by
`SchemaDefinition.from_dict()`. It does not yet map table values into
business-specific `UserConfig` packet/cell semantics or directly populate
`CellConfig`.

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
payload file loading and serialization boundaries
trace/dump/log rendering helpers
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

The outer orchestration package and result model are implemented as:

```text
rm_ref.runtime
OrchestrationResult
```

The implemented runtime boundaries are:

```text
caller injects one explicit SchemaDefinition
caller injects one already constructed Algorithm instance
runtime accepts optional payload_by_packet[packet_index][cell_index]
missing payload entries use []
extra payload indexes and malformed mappings are setup errors
ValidationIssue and ValidationResult use stable plain-data to_dict()
```

The schema, algorithm, and in-memory payload contracts are implemented.
Payload file formats, algorithm registries, CLI policy, and result directories
remain outside runtime.

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
163 passed with explicit PYTHONPATH=src
```

Pytest 6.2.4 warned that it does not recognize the current `pytest.ini`
`pythonpath` option. A static compatibility checker and explicit compatible
import-path setup remain implementation work.

The `runtime-orchestration-v1` task is merged.

The `uvm-table-schema-adapter-v1` task is merged. The implemented boundary is:

```text
uvm_table_printer text
  -> existing UVM table parser
  -> RM schema dict
  -> SchemaDefinition.from_dict()
```

Runtime integration, direct `CellConfig` population from table text,
`UserConfig` generation, payload injection from interface tables, and Chinese
description rule parsing remain future work.

The `p2b-uvm-table-runtime-boundary` task is implemented and independently
reviewed with an `APPROVE WITH FOLLOW-UP` disposition. The implemented
formal UVM table runtime boundary proves:

```text
uvm_table_printer text
  -> rm_ref.io.uvm_table parser
  -> UserConfig-compatible dict
  -> rm_ref.runtime.run_uvm_table_text_case()
  -> rm_ref.runtime.run_case()
  -> Algorithm cell parameter visibility
```

The parser JSON boundary is also exposed through
`run_uvm_table_json_case()`. Both wrappers return `UvmTableCaseResult` and
preserve the inner `OrchestrationResult` from `run_case()` without reinterpreting
runtime PASS, validation, setup, or execution status.

`rm_ref.io.uvm_table.parser` is now a formal package boundary. The config
adapter boundary currently wraps the stabilized P2A implementation to avoid a
second long-lived copy; completing that migration into `src/rm_ref/io` remains
a cleanup item.

The focused smoke passes under the default Python environment and under the
local Python 3.6.3 interpreter when `PYTHONPATH=src` is set explicitly. The
known pytest 6.2.4 `pythonpath` option warning remains an import-path cleanup
follow-up.

The review identified two tracked follow-ups: make the UVM adapter/parser
package boundary independent of the repository-level `utils` layout, and make
Python 3.6 pytest imports reliable without the newer pytest `pythonpath`
option.

The P3A architecture document now defines a pure-Python testcase script contract,
deterministic constrained field randomization, a generic packet-word data
model, and a shared packet-hex v1 format for RTL input, RM intermediate/final
artifacts, DUT actual output, and comparison. Independent review returned
`CHANGES REQUIRED`: the architecture needs explicit no-manifest actual-data
comparison behavior, Python-3.6-safe provenance ordering, and physical stream
grouping rules, plus three minor contract clarifications. This is currently
design work;
the case DSL, randomizer, packer, codec, and comparison implementation do not
yet exist.

## Historical Note

Earlier snapshots and journal entries may describe the UVM parser as pending.
Both the Python-output parser and hierarchical JSON output were merged before
this snapshot.
