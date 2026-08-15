# P2B UVM Table Runtime Boundary Review

## Verdict

**APPROVE WITH FOLLOW-UP**

Commit `33306bc` provides both requested UVM-table entry points and preserves
the existing `run_case()` outcome inside `UvmTableCaseResult` as
`orchestration_result`.  The implementation is appropriate to merge provided
the import/package-boundary and Python 3.6 test-path follow-ups below are
tracked.  No blocker was found in the tested text/JSON-to-algorithm path.

## Evidence Reviewed

- `33306bc` relative to `33306bc^`.
- `src/rm_ref/runtime/uvm_table_case.py` and runtime exports.
- `src/rm_ref/io/uvm_table/` parser and config-adapter boundary.
- Existing `utils/uvm_table_config_adapter.py`, schema fixture, and the P2B
  system test.
- Runtime result/runner contracts and the UVM adapter's reserved/payload
  behavior.

## Strengths

- `run_uvm_table_text_case()` parses text, delegates to the JSON wrapper, and
  both wrappers call the existing `run_case()` once a `UserConfig` is formed.
  They do not duplicate validation, payload mapping, packet/cell traversal, or
  algorithm execution.
- `PASS`, `VALIDATION_ERROR`, and `EXECUTION_ERROR` remain the status of the
  nested, unmodified `OrchestrationResult`.  Parse/binding/config failures are
  stopped before the algorithm runs and retain their messages/reports.
- No `src/rm_ref/core/` file changed and core has no UVM-table imports.  The
  UVM-specific parsing/binding code remains outside core.
- The system tests exercise text and JSON inputs, parse/binding/config failure
  gates, validation and algorithm failures, serialization, and ensure reserved
  fields plus the payload placeholder are absent from algorithm parameters.

## Findings

- **MINOR — Boundary result is an envelope, not an `OrchestrationResult`.**
  The public wrapper result has the new `PARSE_ERROR`, `BINDING_ERROR`,
  `CONFIG_ERROR`, and `RUNTIME_COMPLETED` statuses.  This does not alter
  `run_case()` semantics because its actual result is retained verbatim in
  `orchestration_result`, but callers must unwrap it to use the existing status
  contract.  The API documentation should state this explicitly.

- **MINOR — `rm_ref.io.uvm_table.config_adapter` imports a top-level `utils`
  module.**  The production-facing IO boundary is a re-export of
  `utils.uvm_table_config_adapter`; that utility also mutates `sys.path` on
  import.  It is not a CLI invocation, and the reviewed tests show no accidental
  CLI execution, but this makes the installed/imported-package boundary depend
  on the repository layout and leaves two parser implementations
  (`utils.parse_uvm_table_print` and `rm_ref.io.uvm_table.parser`) to keep in
  sync.  Follow up by defining one supported importable adapter/parser home and
  testing it outside the repository root.

- **MINOR — Python 3.6 pytest import path remains environment-dependent.**
  The Python 3.6 focused suite passes only with `PYTHONPATH=src`.  Without it,
  collection fails with `ModuleNotFoundError: No module named 'rm_ref'`.
  Python 3.6's installed pytest also warns that `pytest.ini`'s `pythonpath`
  option is unknown.  This is a test/bootstrap limitation rather than an
  unsupported syntax finding, but it should be fixed before relying on the
  legacy environment for CI.

- **INFO — Error coverage can be broadened.**  The wrappers correctly retain
  `run_case()` validation and execution results.  Add later tests for a
  wrapper-mediated `SETUP_ERROR` (invalid `payload_by_packet`) and for an
  unexpected `UserConfig.from_dict` failure, whose broad `except Exception`
  currently converts any such exception into `CONFIG_ERROR`.

## Test Results

- `python -m pytest -q tests/test_integration/system_cases/uvm_table_printer_to_algorithm`
  — **10 passed**.
- `python -m pytest -q tests/test_utils` — **65 passed**.
- `python -m pytest -q` — **197 passed**.
- `$env:PYTHONPATH='src'; D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q tests/test_integration/system_cases/uvm_table_printer_to_algorithm`
  — **10 passed**; emitted pytest warnings for unsupported `pythonpath` and
  unavailable cache writes.
- The same Python 3.6 command without `PYTHONPATH=src` — **collection error**:
  `ModuleNotFoundError: No module named 'rm_ref'`.

## Python 3.6 Compatibility

The new runtime and IO modules use Python 3.6-compatible classes, exception
syntax, imports, comprehensions, and standard-library APIs.  The Python 3.6
focused execution with `PYTHONPATH=src` passed.  The outstanding compatibility
issue is test import configuration, not source syntax.

## Scope and Layering Assessment

The reviewed commit's source/test changes are confined to the intended runtime
boundary, IO UVM parser adapter, UVM utility adapter import, and system fixture
coverage; it does not alter core contracts.  Reserved fields are skipped by the
adapter and payload nodes are reported/skipped rather than bound into normal
packet/cell values.  `payload_by_packet` is passed through to `run_case()`;
there is no new payload injection mechanism.

The top-level `utils` dependency is the one layering concern requiring a
follow-up; it should not be allowed to turn into a packaging or second-source
of-truth problem.

## Recommended Disposition

**APPROVE WITH FOLLOW-UP.** Merge is acceptable based on the tested boundary
semantics and core isolation.  Track the two MINOR follow-ups: make the UVM
adapter/parser import boundary package-safe and make Python 3.6 test imports
reliable without relying on the newer pytest `pythonpath` option.
