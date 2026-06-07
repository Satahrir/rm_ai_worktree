# Project Progress Snapshot

## Purpose

This document is a historical overview. It is not the authoritative source for
the active task.

For the current assignment, read:

```text
agents/project_status.json
docs/architecture/97_current_task.md
```

## Project

The repository is a clean rebuild of a Python Reference Model framework for
communication-link verification. It targets Python 3.6.3 and FPGA/UVM/SystemVerilog
verification environments.

The intended flow is:

```text
schema / user config
  -> resolved config
  -> validation
  -> optional packing
  -> core config and runtime context
  -> cell algorithm execution
  -> result / trace / dump
```

## Completed Milestones

- Multi-level `AGENTS.md` files and role prompts were introduced.
- The core execution stage was implemented and merged.
- Core pytest coverage was added and merged.
- Schema, config, and validator support was implemented and merged.
- Cache files were removed from version control and ignore rules were added.

## Current Planned Feature

The next feature is a hierarchical UVM table-printer parser utility. It must
preserve paths such as:

```text
packet_param.header0.packet_type
packet_param.header1.packet_type
```

It is a utility feature and must not modify RM core packages.

## Known Workflow State

At the time of this snapshot:

- `main` is the integration branch.
- Feature development must occur in a dedicated branch and worktree.
- The UVM parser branch/worktree must be created before implementation.
- Shared status files are owned by the integration coordinator.

## Historical Use Only

Do not copy a branch, worktree, allowed path, or task status from this
snapshot. Those values may be stale. Use the authoritative JSON status and
run workflow preflight instead.
