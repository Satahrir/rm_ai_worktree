# P1-A1 Payload Ownership Agent Prompt

## Role

You are the RM P1-A1 payload ownership agent. Perform one behavior-preserving,
Python-3.6-compatible micro-refactor. Do not continue into later Phase 1 work.

Before implementation, follow the repository startup sequence and run:

```powershell
python scripts/agent_workflow.py preflight
```

Stop without modifying files if preflight reports an error.

## Goal

Make `PacketContext` own independently copied per-cell runtime payload working
data. Make each `CellContext` reference the corresponding `PacketContext`
working payload.

Preserve this ownership flow:

```text
PacketConfig.input_pkt_by_cc
        |
        | per-cell deepcopy
        v
PacketContext runtime working payload
        |
        | reference
        v
CellContext input["samples"]
        |
        v
Algorithm.execute_cell()
```

The refactor must preserve:

```text
caller payload isolation
static PacketConfig isolation
packet isolation
cell-to-cell isolation
```

## Implementation Contract

- In `_initialize_packet_context`, build the runtime `packet_by_cc` mapping by
  deep-copying each top-level cell payload independently.
- Do not use `deepcopy(whole_mapping)` for this boundary. A whole-mapping copy
  can preserve a mutable alias shared by two source keys; independently copy
  each cell payload instead.
- Preserve extra keys already present in `PacketConfig.input_pkt_by_cc`.
- Preserve missing active-cell input behavior as `[]`, with independent
  mutable empty lists for different missing cells.
- In `_initialize_cell_context`, obtain samples from
  `packet_ctx.runtime["input"]["packet_by_cc"]`, not from
  `packet_ctx.packet_cfg.input_pkt_by_cc`.
- `CellContext` must directly reference its cell's `PacketContext` working
  payload. Do not perform a second payload `deepcopy()` there.
- Do not remove or change unrelated copies, including caller-boundary payload
  injection, config construction, or parameter copying.
- Do not change the algorithm contract:

```python
class Algorithm(object):
    def execute_cell(self, cell_ctx):
        raise NotImplementedError
```

## Allowed Scope

Modify only:

```text
src/rm_ref/core/lifecycle.py
tests/test_core/test_runner.py
```

## Forbidden Scope

Do not modify:

```text
src/rm_ref/core/config.py
src/rm_ref/core/context.py
src/rm_ref/runtime/
src/rm_ref/config/
tests/test_config/
tests/test_integration/
```

The authoritative status defines the complete boundary. Stop and report if
the goal cannot be completed within it.

## Non-Goals

Do not implement any of the following in this task:

```text
Static Config refactor
CellContext public API redesign
ResolvedConfig changes
Algorithm Registry
UVM/Input Boundary
Packet codec
SRS/PUSCH/PRACH
```

These may be follow-up work, but they are not part of P1-A1.

## Tests

Add behavior-focused tests, not assertions about `deepcopy()` call counts.
At minimum, prove:

- Algorithm mutation does not modify the static `PacketConfig` payload.
- Two cells initialized from the same mutable source object do not contaminate
  each other.
- Missing payload behavior remains `[]`.
- Existing regression tests remain unchanged and pass.

Run:

```powershell
python -m pytest -q tests/test_core/test_runner.py
python -m pytest -q tests/test_core tests/test_config tests/test_integration
python -m pytest -q
```

Then run under Python 3.6.3:

```powershell
$env:PYTHONPATH='src'
D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q tests/test_core tests/test_config tests/test_integration
D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q
```

Finally run:

```powershell
python scripts/agent_workflow.py check-scope
git diff --check
```

Do not delete, weaken, or skip existing tests.

## Completion

Report the baseline, files changed, ownership behavior before and after, tests
added, all validation results, limitations, and follow-up needed. Stop after
P1-A1 and wait for review. Do not update workflow status or journal files.
