# UVM Table Config Adapter

## Purpose

`utils/uvm_table_config_adapter.py` binds values from existing
`uvm_table_printer` parser output into an RM `UserConfig`-compatible JSON
document.

Implemented flow:

```text
uvm_table_printer text
  -> utils.parse_uvm_table_print.parse_uvm_table_tree()
  -> SchemaDefinition
  -> UserConfig-compatible dict
  -> ConfigResolver.resolve()
  -> ResolvedConfig.to_core_config()
  -> PacketConfig / CellConfig parameters
```

The adapter does not call `run_case()`, execute algorithms, inject payload
data, or create runtime results.

## Inputs

The adapter accepts either:

```text
--input <uvm_table_printer text>
--json-input <pre-rendered parser JSON>
```

It also requires:

```text
--schema <schema JSON accepted by SchemaDefinition.from_dict()>
```

The text parser is not reimplemented. Text input is parsed by the existing
`utils.parse_uvm_table_print` utility.

## Matching

Input leaf rows are matched to schema fields in this priority order:

```text
1. scope + word + msb + lsb + raw name
2. scope + word + raw name
3. unique raw name
```

This is required because interface tables can contain duplicate raw names such
as:

```text
FreqDomainPos
Csrs
BSrs
```

If matching is ambiguous, the adapter records an `ambiguous_field` error and
does not bind the value.

## Scope Mapping

First version scope support:

```text
packet -> packets[].values
cell   -> packets[].cells[].values
```

The adapter reads scope rules from schema metadata when present and allows CLI
overrides:

```powershell
--scope-rule demo2=cell
```

If no packet/cell indexes are present in the parser JSON, the adapter uses:

```text
packet_index = 0
cell_index = 0
```

Callers can override the defaults:

```powershell
--default-packet-index 2 --default-cell-index 3
```

If multiple roots with the same table name appear without explicit context
indexes, the adapter reports `missing_required_context`.

## Value Conversion

Supported value forms:

```text
int values
decimal strings: 10
hex strings:     0x1f
binary strings:  0b1010
```

The existing text parser already converts SystemVerilog literals in text input
before this adapter sees them. Pre-rendered JSON values such as `'h1f` are not
required in this first binding layer and are reported as `unsupported_format`.

Converted values are checked against schema width:

```text
0 <= value <= (2 ** width) - 1
```

Overflow is reported as `range_error`.

## Reserved And Payload

Reserved schema fields are skipped and counted in:

```text
skipped_reserved_count
```

Payload placeholders and dynamic-array payload nodes are skipped and counted in:

```text
skipped_payload_count
```

Payload data is not bound into `UserConfig` and this utility does not implement
`payload_by_packet` injection.

## CLI

Example:

```powershell
python utils/uvm_table_config_adapter.py `
  --input tests/fixtures/uvm_table_print/demo2_schema_input_candidate.txt `
  --schema schema_defs/uvm_table/demo2_schema.json `
  --scope-rule demo2=cell `
  --config-output schema_defs/uvm_table/demo2_rm_user_config.json `
  --report-output schema_defs/uvm_table/demo2_config_adapter_report.json
```

## Report

The report JSON includes:

```text
schema_id
input_field_count
bound_field_count
skipped_reserved_count
skipped_payload_count
unknown_field_count
ambiguous_field_count
type_error_count
range_error_count
unsupported_format_count
missing_context_count
warnings
errors
bound_fields
skipped_fields
```

## Generated Demo Files

The committed demo files are:

```text
schema_defs/uvm_table/demo2_rm_user_config.json
schema_defs/uvm_table/demo2_config_adapter_report.json
```

Tests verify that these generated files still match the current adapter output.

## Known Limitations

- Runtime execution is not implemented here.
- `run_case()` integration is not implemented here.
- Algorithm selection and execution are not implemented here.
- `payload_by_packet` injection is not implemented here.
- Chinese description parsing, enum rule extraction, and validator business
  rule generation are not implemented here.
- The first context model supports explicit `packet_index` / `cell_index`
  metadata if present, otherwise a single default packet/cell context.
