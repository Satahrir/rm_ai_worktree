# docs/AGENTS.md

## Documentation role

This directory contains project documentation.

The documentation must help future agents and developers understand:

- project scope
- architecture boundaries
- current implemented behavior
- intended future behavior
- known limitations
- open questions

## Directory layout

```text
docs/reference/
  Historical or reference architecture documents.
  These documents are useful input but are not mandatory implementation specs.

docs/architecture/
  Architecture documents for the clean rebuild.

docs/review/
  Review reports, risk analysis, and suggested follow-up tasks.

docs/interface/
  Boundary utility and external interface documentation.
```

## Reference documents

Documents under `docs/reference/` are reference material.

They may describe an older implementation, an earlier design, or a prototype.

Do not assume everything in `docs/reference/` must be copied exactly.

When using reference documents, extract stable principles such as:

- config and runtime separation
- packet/cell lifecycle
- algorithm contract
- diagnostic propagation
- result structure
- schema/config boundary

Do not blindly copy old names, old import paths, or old implementation details.

## Architecture documents

Documents under `docs/architecture/` describe the clean rebuild.

They should be written as design documents, not marketing documents.

Prefer clear sections:

```text
1. Purpose
2. Current status
3. Design goal
4. Non-goals
5. Data model
6. Execution flow
7. Dependency direction
8. Extension points
9. Known limitations
10. Open questions
```

## Current behavior vs planned behavior

Always distinguish:

```text
Implemented:
  Behavior already present in code and covered by tests.

Designed:
  Intended behavior, but not fully implemented yet.

Planned:
  Future direction, not part of current behavior.

Limitation:
  Known restriction or missing ability.
```

Do not describe planned behavior as if it already exists.

If the code is not implemented yet, say so clearly.

## Documentation style

Use simple, direct language.

Prefer diagrams in plain text.

Good:

```text
UserConfig
  -> Resolver
  -> ResolvedConfig
  -> Validator
  -> Core TestcaseConfig
  -> Runner
```

Avoid ambiguous phrases such as:

```text
The system automatically handles everything.
```

Instead, explain what module owns what behavior.

## Architecture boundaries to preserve

The clean rebuild should preserve these boundaries:

```text
Config:
  Describes static execution input.

Context:
  Holds runtime state, diagnostics, trace, and output.

Execution:
  Drives packet/cell lifecycle.

Algorithm:
  Implements business model calculation for one cell.

Schema:
  Describes external interface fields.

Resolver:
  Converts user input plus schema defaults into deterministic resolved config.

Validator:
  Checks resolved config before execution or packing.

Packer:
  Packs validated values into hardware words.

IO:
  Loads payload and serializes outputs.

Observability:
  Handles trace, dump, and log rendering.
```

## Review documents

Review reports should live in:

```text
docs/review/
```

A review report should include:

```text
1. Summary
2. Files reviewed
3. Major risks
4. Minor issues
5. Python 3.6 compatibility issues
6. Layering violations
7. Missing tests
8. Suggested next steps
```

Review agents should not silently modify source code unless explicitly requested.

## Do not

Do not use documentation to hide implementation gaps.

Do not claim tests pass unless tests were actually run.

Do not describe private assumptions as facts.

Do not rewrite reference documents unless explicitly asked.

Do not move documents between directories without a clear reason.
