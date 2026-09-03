# Phase 1 Refactor Agent Prompt

## Role

You are the RM Phase 1 refactor agent. Perform a behavior-preserving,
Python-3.6-compatible hardening pass across the existing runtime, core, and
configuration boundary. Do not redesign the framework or expand into protocol
logic.

Before implementation, run:

```powershell
python scripts/agent_workflow.py preflight
```

Stop if preflight reports any error.

## Goal

Harden three existing contracts, in this priority order:

```text
1. runtime payload ownership
2. static config mutation
3. CellContext public API
```

Preserve the existing vertical flow and public behavior:

```text
UserConfig -> ConfigResolver -> ResolvedConfig -> validation
  -> to_core_config -> runtime -> core.run_config -> pipeline
  -> PacketContext -> CellContext -> Algorithm.execute_cell(cell_ctx)
  -> CellOutput / PacketOutput / RunResult
```

## Required Behavior

### Payload Ownership

- Trace `payload_by_packet` through runtime mapping, `PacketConfig`,
  `PacketContext`, `CellContext`, and the algorithm boundary.
- Remove only redundant large-object deep copies.
- Retain one explicit isolation boundary wherever mutable algorithm input must
  be protected.
- Ensure packet and cell payloads cannot leak into one another.
- Define and test whether the original caller payload remains unchanged.

### Static Config

- `PacketConfig` construction must not silently mutate caller-owned
  `CellConfig` objects.
- `TestcaseConfig` construction must not silently mutate caller-owned
  `PacketConfig` objects.
- Normalized indexes must remain deterministic through resolved-to-core
  conversion and repeated conversion.
- Static config must not change during execution.
- Prefer explicit new objects over hidden cross-object normalization; do not
  introduce an immutability framework.

### CellContext Contract

- Algorithms should use the existing public context accessors for config,
  input, derived data, output, and diagnostics.
- Add only small protocol-neutral accessors that are demonstrably missing.
- Keep `runtime` available as framework representation; do not make it private
  in this phase.
- Do not change `Algorithm.execute_cell(cell_ctx)`.

## Allowed Scope

Modify only the paths declared in the authoritative active-task status. The
intended source and test scope is:

```text
src/rm_ref/core/
src/rm_ref/config/
src/rm_ref/runtime/
tests/test_core/
tests/test_config/
tests/test_integration/
```

## Non-Goals

Do not modify or redesign:

```text
schema
validator
packer
packet codec or packet value model
SRS/PUSCH/PRACH algorithms
UVM table parsing
file formats or CLI policy
dependency or packaging metadata
```

Do not add third-party runtime dependencies, large abstraction layers, broad
formatting, file moves, or renames. Splitting the resolved-to-core adapter is
optional and should be deferred if it broadens public API changes.

The packet value/codec task `p3b-packet-value-codec-v1` remains a lower
priority follow-up and is outside this task.

## Work Sequence

1. Record the full-test baseline.
2. Add behavior-focused ownership tests before production changes.
3. Refactor payload copies and run core/integration tests.
4. Add static-mutation tests before production changes.
5. Refactor config construction and run core/config/integration tests.
6. Tighten and test the context public contract.
7. Run focused tests, full regression, Python 3.6.3 regression, and scope
   checking.

## Completion

Run:

```powershell
python -m pytest -q tests/test_core tests/test_config tests/test_integration
python -m pytest -q
$env:PYTHONPATH='src'; D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q tests/test_core tests/test_config tests/test_integration
$env:PYTHONPATH='src'; D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q
python scripts/agent_workflow.py check-scope
git status --short
```

Report baseline, files changed with reasons, old and new payload paths,
remaining copies and their ownership reasons, removed config mutations,
recommended CellContext API, tests added, regressions, limitations, and Phase
2 follow-up. Stop after Phase 1. Do not update shared workflow status or the
journal. Do not commit unless explicitly requested.
