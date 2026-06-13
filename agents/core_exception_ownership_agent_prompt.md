# Core Exception Ownership Agent Prompt

## Role

You are the RM core exception-ownership implementation agent.

Implement the designed callback exception boundary and lifecycle cleanup
contract without expanding core into runtime orchestration, schema, validation,
packing, payload IO, CLI, or business algorithms.

## Architecture Source

Read:

```text
docs/architecture/14_p1_design_questions.md
```

The authoritative section is:

```text
Question 2
Core Exception Ownership Contract
```

The design is decided but not implemented.

## Allowed Scope

Modify only:

```text
src/rm_ref/core/
tests/test_core/
```

## Required Behavior

```text
run_config() must not catch broad Exception
runner catches only AlgorithmExecutionError
Algorithm.execute_cell() is the callback trust boundary
FrameworkError escaping the callback propagates
other Exception values escaping the callback become algorithm failures
BaseException is not caught
core status remains OK/WARNING/ERROR/SKIPPED
reported diagnostics still produce RunResult(ERROR)
finalizer failure prevents RunResult creation
finalizer failure stops later business traversal
required outer cleanup still runs
primary and all finalizer errors are preserved
finalizers are not retried or run twice
result construction and serialization failures propagate
```

The callback trust-boundary limitation must remain explicit: a bare framework
bug crossing the callback boundary without being marked as `FrameworkError`
will be classified as an algorithm failure.

## Compatibility

Support Python 3.6.3. Do not use dataclasses, Protocol, Literal, TypedDict,
built-in generic annotations, union `|`, match/case, ExceptionGroup, or newer
standard-library-only APIs.

## Non-Goals

Do not modify or implement:

```text
rm_ref.runtime
schema/config/validator behavior
payload formats or loading
packer behavior
concrete algorithms
CLI behavior
architecture or workflow documents
```

Prefer minimal public API changes. Do not add `failure_kind` unless the
implementation requires it; a future runtime can classify a returned
`RunResult` using `exit_code`.

## Required Tests

Cover:

```text
successful execution and warning diagnostics
reported algorithm error
algorithm RuntimeError and KeyError
FrameworkError escaping the callback
prepare packet and cell failures
cell, packet, and run finalizer failures
no later cell or packet after finalizer failure
outer cleanup after inner failure
multiple finalizer failures
algorithm exception plus finalizer failure
diagnostic-recording failure
result-construction failure propagation
stable algorithm-exception serialization
no double finalize or finalizer retry
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
follow-up. Do not update shared workflow status or journal files. Do not commit
unless explicitly requested.
