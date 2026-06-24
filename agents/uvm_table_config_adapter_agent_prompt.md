# UVM Table Config Adapter Agent Prompt

## Role

You are the UVM table config adapter implementation agent.

Your job is to add the first minimal value-binding boundary between the
existing UVM table-printer parser/schema utilities and the RM config layer:

```text
uvm_table_printer text / parser JSON
  -> SchemaDefinition
  -> RM UserConfig-compatible dict
  -> UserConfig / ConfigResolver / ResolvedConfig.to_core_config()
```

This task must not run algorithms, call `run_case()`, inject payload data, or
modify runtime orchestration.

## Assigned Worktree

Implement only from the assigned feature worktree:

```text
rm_ref_uvm_config
codex/uvm-config
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

Implement a value adapter that consumes existing parser generic JSON, matches
leaf values against an injected `SchemaDefinition` or schema dict, and emits an
RM `UserConfig.from_dict()` compatible dict.

The minimum smoke path is:

```text
config_dict
  -> UserConfig.from_dict()
  -> ConfigResolver.resolve(schema=SchemaDefinition)
  -> ResolvedConfig.to_core_config()
  -> CellConfig.parameters / PacketConfig.parameters
```

Do not reimplement the UVM table text parser. Reuse
`utils.parse_uvm_table_print`.

## Matching Rules

Do not match fields only by raw name unless the raw name is unique.

Use this priority:

```text
1. scope + word + msb + lsb + raw_name
2. scope + word + raw_name
3. unique raw_name
```

If a match is ambiguous, record an ambiguous field and fail conversion or return
a report with errors. Do not silently choose the first candidate.

## Scope Rules

First version scope support:

```text
packet -> packets[].values
cell   -> packets[].cells[].values
```

If the input has no explicit packet/cell indexes, use:

```text
packet_index = 0
cell_index = 0
```

If the input clearly represents multiple packet/cell contexts without enough
boundary metadata, report a fatal missing-context error instead of silently
merging values.

## Values

Support at least:

```text
10
0x1f
0b1010
int values
```

Do not require SystemVerilog literal support in this task. If unsupported
formats such as `'h1f` or `8'hff` are not handled, report them clearly.

Validate converted values against field width:

```text
0 <= value <= (2 ** width) - 1
```

Reserved fields must not enter normal user config values. Default policy is to
skip reserved fields and count them in the report.

Payload ranges/placeholders must not enter normal config values. Do not
implement `payload_by_packet` injection.

## Report

Generate deterministic report data with at least:

```text
input_field_count
bound_field_count
skipped_reserved_count
skipped_payload_count
unknown_field_count
ambiguous_field_count
type_error_count
warnings
errors
```

The report should distinguish unknown fields, ambiguous fields, type errors,
range errors, unsupported value formats, and missing required context.

## Suggested Outputs

Add generated examples under:

```text
schema_defs/uvm_table/
```

Suggested names:

```text
demo2_rm_user_config.json
demo2_config_adapter_report.json
```

The files should be deterministic and suitable for diff review.

## Tests

Add focused tests under:

```text
tests/test_utils/
```

Required tests:

```text
test_uvm_json_values_to_rm_config_single_packet_single_cell
test_duplicate_raw_name_requires_stable_schema_match
test_ambiguous_raw_name_fails_or_reports_error
test_reserved_field_is_skipped_from_user_config
test_payload_range_is_not_bound_to_cell_config
test_value_type_conversion_decimal_hex_binary
test_value_width_overflow_is_reported
test_default_packet_cell_index_for_single_context
test_missing_context_for_multi_context_is_reported
```

Keep tests Python 3.6.3-compatible.

## Documentation

Add or update documentation under:

```text
docs/interface/
```

Document:

```text
input assumptions
matching priority
scope-to-UserConfig mapping
default packet/cell index policy
reserved and payload skipping
value conversion support
report fields
known limitations
```

Do not describe runtime integration or algorithm execution as implemented.

## Non-Goals

Do not implement:

```text
core.run_config()
run_case() end-to-end integration
algorithm execution
payload_by_packet injection
Chinese description rule parsing
validator business rule generation
OrchestrationResult or runtime status changes
large parser/schema-adapter refactors
```

## Completion Checklist

Run:

```powershell
python -m pytest -q tests/test_utils
python utils/parse_uvm_table_print.py --help
python utils/uvm_table_schema_adapter.py --help
python utils/uvm_table_config_adapter.py --help
python scripts/agent_workflow.py check-scope
git status --short
```

Run `python -m pytest -q` when reasonable. If Python 3.6.3 verification is
practical, use:

```powershell
$env:PYTHONPATH='src'
D:\ProgramData\miniconda3\envs\py3p6\python.exe -m pytest -q tests/test_utils
```

Final summary should include changed files, CLI usage, generated config/report
examples, tests run, failures, limitations, and follow-up.
