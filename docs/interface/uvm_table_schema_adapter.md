# UVM Table Schema Adapter

## Purpose

`utils/uvm_table_schema_adapter.py` compiles existing
`uvm_table_printer` parsed hierarchy into an RM schema JSON document accepted
by:

```python
SchemaDefinition.from_dict(schema_dict)
```

The adapter is a utility boundary. It does not run RM algorithms, build
`UserConfig`, call `run_case()`, load payload files, or choose algorithms.

## Flow

The supported flow is:

```text
uvm_table_printer text
  -> utils.parse_uvm_table_print.parse_uvm_table_tree()
  -> utils.uvm_table_schema_adapter
  -> RM schema dict JSON
  -> SchemaDefinition.from_dict()
```

The adapter reuses the existing UVM table parser. It does not implement a
second text parser.

## Input Format

The text input follows the existing table-printer columns:

```text
Name                         Type                Size    Value
```

For schema compilation, bit ranges are carried in the `Type` column:

```text
FreqDomainPos                integral[31:23]     9       'h000
```

`wordN` rows are word markers:

```text
word1                        integral[31:0]      32      'h00000000
```

They update the current word index and are not emitted as normal schema
fields.

## Scope Rules

Schema scope is configured outside the table parser.

Example:

```powershell
--scope-rule demo2=cell
```

The current demo fixture uses:

```text
demo2 -> cell
```

If a root table has no matching scope rule, compilation fails. The adapter does
not silently guess `global`, `packet`, or `cell`.

## Naming

Generated field names include scope, header path, word, and bit position:

```text
<scope>.<header_path>.<raw_name>__w<word>_b<msb>_<lsb>
```

Examples:

```text
cell.header0.FreqDomainPos__w1_b31_23
cell.header1.Csrs__w7_b23_16
```

The source field name is preserved as `original_name`.

## Reserved Fields

Reserved fields are kept in the schema with:

```json
"reserved": true
```

Keeping them allows later bit-table coverage or reserved-bit checks. Future
`UserConfig` generation can skip reserved fields separately.

## Payload Placeholders

Payload placeholders are not normal schema fields. Nodes named `Payload` or
with a dynamic-array type such as `da(integral)` are recorded in report data
with reason `runtime_payload`.

## CLI

Compile from table-printer text:

```powershell
python utils/uvm_table_schema_adapter.py `
  --input tests/fixtures/uvm_table_print/demo2_schema_input_candidate.txt `
  --schema-id demo2/schema/v1 `
  --scope-rule demo2=cell `
  --schema-output schema_defs/uvm_table/demo2_schema.json `
  --report-output schema_defs/uvm_table/demo2_schema_report.json
```

Compile from pre-rendered generic JSON:

```powershell
python utils/uvm_table_schema_adapter.py `
  --json-input schema_defs/uvm_table/demo_generated_table.json `
  --schema-id demo2/schema/v1 `
  --scope-rule demo2=cell `
  --schema-output schema_defs/uvm_table/demo2_schema.json `
  --report-output schema_defs/uvm_table/demo2_schema_report.json
```

## Report

The report JSON includes:

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
payload_ranges
```

The report is the place for skipped payload nodes and conversion diagnostics
that do not belong in `SchemaDefinition` fields.

## Generated Demo Files

The committed demo files are:

```text
tests/fixtures/uvm_table_print/demo2_schema_input_candidate.txt
schema_defs/uvm_table/demo2_schema.json
schema_defs/uvm_table/demo2_schema_report.json
```

Tests verify that the generated files still match the current adapter output.

## Known Limitations

- The adapter expects bit ranges in the `Type` column.
- Chinese descriptions, enum text, range notes, and dependency rules are not
  parsed.
- Runtime integration, payload injection, and `UserConfig` generation are not
  implemented here.
- The adapter currently uses root table names for scope rules; richer source
  metadata can be added to the parser JSON later without changing the schema
  layer.
