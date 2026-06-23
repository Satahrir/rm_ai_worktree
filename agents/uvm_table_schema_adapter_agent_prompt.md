# UVM Table Schema Adapter Agent Prompt

## Role

You are the UVM table schema adapter implementation agent.

Your job is to add the first schema compiler boundary between the existing
generic UVM table-printer parser output and the RM schema layer:

```text
uvm_table_printer text
  -> existing parser generic JSON / parsed tree
  -> RM schema dict
  -> SchemaDefinition.from_dict()
```

This is an interface/schema utility task. Do not connect runtime execution,
`run_case()`, payload injection, algorithm selection, or `UserConfig`
generation.

## Assigned Worktree

Implement only from the assigned feature worktree:

```text
rm_ref_uvm_json
codex/uvm-json
```

Before implementation, run:

```powershell
python scripts/agent_workflow.py preflight
```

Stop if preflight reports any error.

## Allowed Files

You may modify:

```text
utils/
schema_defs/uvm_table/
tests/test_utils/
tests/fixtures/uvm_table_print/
docs/interface/
```

Do not modify:

```text
src/rm_ref/core/
src/rm_ref/runtime/
src/rm_ref/config/
src/rm_ref/validator/
src/rm_ref/packer/
src/rm_ref/algorithms/
tests/test_core/
tests/test_integration/
tests/test_config/
tests/test_validator/
tests/test_packer/
tests/test_algorithms/
docs/architecture/
agents/
scripts/
```

unless explicitly asked through a coordinator status update.

## Primary Task

Implement a schema adapter/compiler that consumes the existing parser's
hierarchical generic JSON shape and emits an RM schema dict accepted by:

```python
SchemaDefinition.from_dict(schema_dict)
```

The adapter must reuse the existing UVM table parser. Do not reimplement the
text parser.

## Input Contract

The accepted text format follows the existing `uvm_table_printer` table style:

```text
Name                         Type                Size    Value
```

For schema compilation, field bit ranges are encoded in the `Type` column:

```text
FreqDomainPos                integral[31:23]     9       'h000
```

The adapter should keep this access encapsulated so future parser JSON can add
fields such as source, comment, access, or category without rewriting the core
compiler.

Current target fixture:

```text
tests/fixtures/uvm_table_print/demo2_schema_input_candidate.txt
```

Production input is UVM table-printer style text. Excel is only reference
material or fixture-generation input.

## Scope Rules

Scope is configuration, not hard-coded compiler behavior.

For this task:

```json
{
  "scope_rules": {
    "demo2": "cell"
  }
}
```

If a source/root table has no rule, fail clearly or report a clear warning only
when an explicit warning policy is selected. Do not silently guess scope.

## Field Rules

`wordN` rows are word markers and must not become schema fields.

Field rows should become schema fields with:

```text
name
original_name
scope
word
msb
lsb
reserved
```

The `width` may be omitted when `msb/lsb` imply it, or included if it matches.
The output must remain compatible with current schema normalization.

Reserved fields stay in the schema with:

```json
"reserved": true
```

Payload ranges or payload placeholders must not become normal schema fields.
Record them in the report or schema metadata.

Do not parse Chinese descriptions, enum descriptions, range notes, or business
rules in this task. Preserve raw text in report/metadata only if available.

## Naming

Use stable names that include scope, hierarchy, word, and bit location:

```text
<scope>.<header_path>.<raw_name>__w<word>_b<msb>_<lsb>
```

Examples:

```text
cell.header0.FreqDomainPos__w1_b31_23
cell.header1.Csrs__w7_b23_16
```

Do not rely on encounter-order suffixes such as `_1` or `_2` for duplicates.
Preserve the original source name as `original_name`.

## Report

Generate deterministic report data with at least:

```text
schema_id
word_width
word_count
field_count
reserved_count
duplicate_raw_name_count
payload_range_count
skipped_field_count
warnings
```

The report should also be the place for payload spans, skipped rows, and extra
source metadata that does not belong in `SchemaDefinition` fields.

## Suggested Outputs

Add generated examples under:

```text
schema_defs/uvm_table/
```

Suggested names:

```text
demo2_schema.json
demo2_schema_report.json
```

The files should be deterministic and suitable for diff review.

## Tests

Add focused tests under:

```text
tests/test_utils/
```

Minimum tests:

```text
test_parse_simulated_uvm_text_to_json
test_uvm_json_to_schema_dict
test_schema_definition_from_dict
test_duplicate_field_naming_is_stable
test_word_markers_are_not_added_as_fields
test_reserved_fields_are_kept
test_payload_range_is_not_added_as_normal_field
test_scope_rules_are_required_or_applied
```

Keep tests Python 3.6.3-compatible.

## Documentation

Add or update documentation under:

```text
docs/interface/
```

Document:

```text
formal input assumptions
Type-column bit range convention
scope_rules
naming strategy
reserved handling
payload skipping
report fields
known limitations
```

Do not describe runtime integration or UserConfig generation as implemented.

## Non-Goals

Do not implement:

```text
runtime integration
run_case() integration
payload_by_packet injection
full UserConfig generation
business validator rule generation
Chinese description rule parsing
algorithm selection
OrchestrationResult or runtime status changes
new UVM text parser
```

## Completion Checklist

Run:

```powershell
python -m pytest -q tests/test_utils
python utils/parse_uvm_table_print.py --help
python utils/uvm_table_schema_adapter.py --help
python scripts/agent_workflow.py check-scope
git status --short
```

Run `python -m pytest -q` when reasonable. If Python 3.6.3 verification is
practical, use the explicit compatible import path:

```powershell
$env:PYTHONPATH='src'
D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q tests/test_utils
```

Final summary should include files changed, APIs/CLI added, tests run,
failures, limitations, and follow-up.
