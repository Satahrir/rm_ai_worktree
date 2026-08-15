# P2B UVM Table Runtime Boundary Review Prompt

## Role

You are the independent review agent for the P2B UVM table runtime boundary.
Review the implementation and write a decision-ready report. Do not modify
source, tests, utilities, schemas, workflow files, or architecture documents.

## Review Target

Review the implementation introduced by commit `33306bc` relative to its
parent. The intended boundary is:

```text
uvm_table_printer text or parser JSON
  -> rm_ref.io.uvm_table boundary
  -> UserConfig-compatible data
  -> run_uvm_table_text_case() / run_uvm_table_json_case()
  -> run_case()
  -> OrchestrationResult
```

## Required Checks

1. Confirm both wrapper APIs preserve the `run_case()` result semantics.
2. Confirm core does not gain UVM-table, schema, or runtime-wrapper coupling.
3. Confirm parser/config adapter reuse does not create conflicting sources of
   truth or require an accidental CLI dependency.
4. Confirm reserved fields and payload placeholders are not exposed as normal
   packet or cell parameters.
5. Confirm expected failures have actionable messages and do not hide framework
   errors behind a new status model.
6. Check Python 3.6.3 syntax and imports, including the known `PYTHONPATH=src`
   issue with the local Python 3.6 pytest environment.
7. Assess focused and full-test coverage; run the assigned checks where
   possible and report exact results.

## Scope

You may write only:

```text
docs/review/p2b_uvm_table_runtime_boundary_review.md
```

## Report Structure

Use these sections:

```markdown
# P2B UVM Table Runtime Boundary Review

## Verdict
## Evidence Reviewed
## Strengths
## Findings
## Test Results
## Python 3.6 Compatibility
## Scope and Layering Assessment
## Recommended Disposition
```

Use `BLOCKER`, `MAJOR`, `MINOR`, or `INFO` labels for findings. State one of:
`APPROVE`, `APPROVE WITH FOLLOW-UP`, or `CHANGES REQUIRED` in the verdict.

## Forbidden Actions

Do not fix code, alter tests, merge branches, update task status, or rewrite
documentation outside the report.
