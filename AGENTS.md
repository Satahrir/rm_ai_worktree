# AGENTS.md

## Project

This repository is a clean rebuild of a Python Reference Model framework for communication link verification.

The project targets RM usage in FPGA/UVM/SystemVerilog verification environments.

The previous architecture document under `docs/reference/` is reference material only. It is not mandatory to copy the old implementation one-to-one.

## Main goal

Build a clean, testable, Python 3.6-compatible RM framework with the following high-level flow:

```text
user config / schema
  -> resolved config
  -> validation
  -> optional word packing
  -> core TestcaseConfig / PacketConfig / CellConfig
  -> RMContext / PacketContext / CellContext
  -> Algorithm execution
  -> diagnostics
  -> result / trace / dump
```

## Core architecture principles

- Static configuration and runtime state must be separated.
- Config describes what to run.
- Context records what happens during execution.
- Algorithms operate on one `CellContext` at a time.
- The pipeline owns packet/cell traversal.
- Validation should happen before algorithm execution when possible.
- Business schema and algorithm-specific fields must not pollute the core execution framework.
- File IO, payload loading, reports, dumps, and CLI behavior must stay outside the deep core unless explicitly designed as boundary modules.

## Python compatibility

This project must support Python 3.6.3.

Do not use:

- `dataclasses`
- `typing.Protocol`
- `Literal`
- `TypedDict`
- `list[str]`, `dict[str, int]`, or other built-in generic syntax
- `X | Y` union syntax
- `match/case`
- f-string debug syntax such as `{var=}`
- APIs that only exist in newer Python versions

Use:

- normal classes
- explicit `__init__`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Union`
- traditional f-strings supported by Python 3.6, or `%` / `.format()`
- explicit exception classes

## Repository layout

```text
docs/reference/
  Old/reference architecture documents.

docs/architecture/
  New architecture documents for this clean rebuild.

src/rm_ref/core/
  Stable RM execution core.

src/rm_ref/schema/
  Schema representation, normalization, and registry.

src/rm_ref/config/
  UserConfig, ResolvedConfig, and resolver.

src/rm_ref/validator/
  Validation rules and validation result model.

src/rm_ref/packer/
  Hardware word packing utilities.

src/rm_ref/io/
  Payload and serialization boundary helpers.

src/rm_ref/observability/
  Trace, dump, and log rendering helpers.

src/rm_ref/algorithms/
  Business algorithms such as demo, SRS, PUSCH, PRACH.

schema_defs/
  Generated or hand-written schema definitions.

utils/
  Schema extraction and generation utilities.

tests/
  Pytest tests.
```

## Dependency direction

Preferred dependency direction:

```text
schema/config/validator/packer
        |
        v
      core contracts
        |
        v
      core execution
        |
        v
      runner/result
```

Important rules:

- `core` must not depend on concrete SRS/PUSCH/PRACH fields.
- `core` must not import schema definitions from `schema_defs`.
- Algorithms may depend on core contracts.
- Validators may depend on schema/config models.
- Packers may depend on schema/config models.
- IO helpers must not control pipeline execution.
- CLI or external tools must remain outside the core package.

## Agent ownership

Each agent must stay in its assigned area.

### Arch agent may modify

- `docs/architecture/`
- `docs/review/` only when explicitly asked

### Core agent may modify

- `src/rm_ref/core/`
- `src/rm_ref/io/` only if needed for payload boundary
- `src/rm_ref/observability/` only if needed for trace/dump boundary
- `tests/test_core/`

### Config agent may modify

- `src/rm_ref/schema/`
- `src/rm_ref/config/`
- `src/rm_ref/validator/`
- `schema_defs/`
- `tests/test_schema/`
- `tests/test_config/`
- `tests/test_validator/`

### Packer agent may modify

- `src/rm_ref/packer/`
- `tests/test_packer/`
- `docs/architecture/08_packer.md` if it exists

### Algorithm demo agent may modify

- `src/rm_ref/algorithms/`
- `tests/test_algorithms/`

### Tests agent may modify

- `tests/`
- `pytest.ini`
- `setup.py` only when needed for imports or test running

### Review agent may modify

- `docs/review/`

### UVM table parser agent may modify

- `utils/`
- `schema_defs/uvm_table/`
- `tests/test_utils/`
- `tests/fixtures/uvm_table_print/`
- `docs/interface/`

### UVM table JSON agent may modify

- `utils/`
- `schema_defs/uvm_table/`
- `tests/test_utils/`
- `tests/fixtures/uvm_table_print/`
- `docs/interface/`

### Workflow coordinator may modify

- `AGENTS.md`
- `agents/`
- `docs/architecture/96_agent_journal.md`
- `docs/architecture/97_current_task.md` through the renderer only
- `docs/architecture/98_project_progress_snapshot.md`
- `docs/architecture/99_multi_agent_workflow.md`
- `scripts/`
- `tests/test_scripts/`
- directory-specific `AGENTS.md` files needed by the workflow

## Do not modify unrelated files

Do not rewrite unrelated modules.

Do not redesign another agent's area unless the user explicitly asks.

Do not silently change public APIs.

Do not rename directories unless explicitly requested.

## Testing

Use pytest.

Main command:

```bash
pytest -q
```

Focused commands:

```bash
pytest -q tests/test_core
pytest -q tests/test_schema
pytest -q tests/test_config
pytest -q tests/test_validator
pytest -q tests/test_packer
pytest -q tests/test_algorithms
pytest -q tests/test_integration
```

Every new behavior should have tests.

Tests must not require:

- internet access
- FPGA hardware
- UVM simulator
- proprietary tools
- external services

## Error message requirements

Validation and packing errors should include:

- field name
- bad value
- expected rule
- schema id if available
- packet index if available
- cell index if available
- word index and bit range if available

## Coding style

Prefer simple, explicit, testable code.

Avoid clever dynamic behavior.

Avoid global mutable state.

Prefer small modules and small functions.

Prefer structured result objects over ambiguous tuples.

Use explicit exceptions for invalid input.

## Runtime state rules

Runtime state belongs in context objects, not static config.

Allowed runtime scopes:

```text
state.*
config.*
derived.*
input.*
output.*
trace.*
```

Avoid arbitrary string keys in critical paths. Prefer constants or accessor methods when paths become stable.

## Algorithm rules

Algorithms should:

- read from `CellContext`
- write outputs to `CellContext`
- record warnings/errors/debug through context APIs
- avoid direct file IO unless explicitly injected
- avoid modifying static config

Algorithms should not:

- drive packet/cell loops
- parse Excel
- parse user config files
- create result directories
- decide CLI exit codes
- build global reports

## Documentation rules

Documentation must distinguish:

- current implemented behavior
- intended design
- known limitations
- future work

Do not describe a planned feature as already implemented.

# Mandatory Startup Sequence

Before doing any work:

1. Read `agents/project_status.json`. This is the authoritative active-task
   status.
2. Read `docs/architecture/97_current_task.md`. This is generated from the
   authoritative status for human readability.
3. Read `agents/README.md`.
4. Read `docs/architecture/99_multi_agent_workflow.md`.
5. Read your role-specific prompt under `agents/`.
6. Read the nearest `AGENTS.md` files for every directory you may modify.
7. Run the workflow preflight from the assigned worktree:

```powershell
python scripts/agent_workflow.py preflight
```

Then summarize:

- current project status
- current task
- actual branch and worktree
- allowed scope
- forbidden scope
- planned work

Do not modify files if preflight reports an error. Resolve the branch,
worktree, missing-file, or dirty-start problem first.

`docs/architecture/96_agent_journal.md` is append-only history.
`docs/architecture/98_project_progress_snapshot.md` is a historical snapshot.
Neither file is an authoritative source for the active task.

---

# Mandatory Finish Sequence

Before stopping, a feature agent must:

1. Run its focused tests.
2. Run the scope check:

```powershell
python scripts/agent_workflow.py check-scope
```

3. Report:

- files changed
- tests run
- failures
- limitations
- follow-up needed

Feature agents must not update shared workflow status files. After review or
merge, the integration coordinator updates `agents/project_status.json`, runs:

```powershell
python scripts/agent_workflow.py render
```

and appends a concise entry to `docs/architecture/96_agent_journal.md`.
