# UVM Table Config Adapter Design Notes

## Purpose

This document records the implementation summary, design reasoning, and
extension points for the P2A task:

```text
uvm_table_printer parser JSON + SchemaDefinition
  -> RM UserConfig-compatible dict
  -> ConfigResolver
  -> ResolvedConfig.to_core_config()
  -> PacketConfig / CellConfig parameters
```

The implementation lives in:

```text
utils/uvm_table_config_adapter.py
```

It is intentionally a utility/boundary module. It does not run RM algorithms,
call `run_case()`, inject payload data, or modify runtime orchestration.

## Implemented Scope

Implemented behavior:

```text
uvm_table_printer text
  -> existing parse_uvm_table_tree()
  -> parser generic JSON
  -> schema-guided value binding
  -> UserConfig-compatible dict
```

The smoke path is covered by tests:

```text
UserConfig.from_dict(config_dict)
  -> ConfigResolver().resolve(user_config, schema=schema)
  -> ResolvedConfig.to_core_config()
  -> CellConfig.parameters
```

The generated demo output is:

```text
schema_defs/uvm_table/demo2_rm_user_config.json
schema_defs/uvm_table/demo2_config_adapter_report.json
```

## Design Principles

### Reuse Existing Parser

The adapter does not parse UVM table text directly. Text input is handled by:

```text
utils.parse_uvm_table_print.parse_uvm_table_tree()
```

This keeps the text grammar in one place and makes this adapter responsible
only for:

```text
parser generic JSON -> RM config dict
```

### Keep Runtime Out

This utility stops at static config construction. Runtime execution remains
outside this layer:

```text
not implemented here:
  run_case()
  algorithm execution
  payload_by_packet injection
  OrchestrationResult status policy
```

This preserves the project boundary where utilities generate data and runtime
modules execute cases.

### Bind Through SchemaDefinition

The adapter accepts either a `SchemaDefinition` or a schema dict accepted by:

```python
SchemaDefinition.from_dict(schema_dict)
```

Schema fields provide the stable contract for:

```text
scope
word
msb
lsb
width
original_name
normalized_name
reserved
```

Output config values use `field.normalized_name`, because `ConfigResolver`
canonicalizes user values through the schema and writes normalized names into
`ResolvedConfig`, then into core `PacketConfig.parameters` or
`CellConfig.parameters`.

Example:

```text
schema name:       cell.header0.packet_type__w0_b31_28
normalized config: cell.header0.packet_type_w0_b31_28
```

The double underscore in generated schema names is normalized by the schema
layer. This is expected and tested.

## Data Flow

### CLI Flow

```text
--input text file
  -> parse_uvm_table_tree()
  -> {"format": "uvm_table_printer/v1", "roots": roots}
  -> bind_config_from_uvm_table_json()
  -> config JSON + report JSON
```

For pre-rendered parser JSON:

```text
--json-input parser.json
  -> bind_config_from_uvm_table_json()
  -> config JSON + report JSON
```

### In-Memory API

Primary API:

```python
bind_config_from_uvm_table_json(
    document_or_roots,
    schema,
    scope_rules=None,
    case_name="uvm_table_config",
    algorithm_name="",
    default_packet_index=0,
    default_cell_index=0,
)
```

Return type:

```text
ConfigBindingResult
  .config_dict
  .report
  .has_errors
```

`has_errors` is true when report errors are present. The CLI returns non-zero
when `has_errors` is true.

## Matching Design

The adapter builds a `_FieldIndex` from `schema.fields` with these indexes:

```text
(scope, word, msb, lsb, original_name)
(scope, word, original_name)
original_name
```

Matching priority:

```text
1. scope + word + msb + lsb + raw name
2. scope + word + raw name
3. unique raw name
```

This avoids relying only on raw names, because demo2 has duplicates such as:

```text
FreqDomainPos
Csrs
BSrs
```

If raw-name fallback finds multiple schema candidates, the adapter records:

```text
code: ambiguous_field
```

and does not bind the value. It never silently chooses the first candidate.

## Scope And Context

Supported scopes in this task:

```text
packet -> packets[].values
cell   -> packets[].cells[].values
```

Scope is resolved from:

```text
1. explicit scope_rules argument / --scope-rule
2. schema.metadata["scope_rules"]
3. single schema field scope fallback
```

Only `packet` and `cell` are supported by this adapter. `global` is not bound
by this P2A task because the requested target was packet/cell config.

Context policy:

```text
packet_index defaults to 0
cell_index defaults to 0
```

If parser JSON includes `packet_index` or `cell_index` on roots or nested
nodes, the adapter propagates those values down the tree. This is a pre-wired
extension point even though the current parser fixture does not emit those
fields.

If multiple roots with the same source table name appear without explicit
context indexes, the adapter reports:

```text
code: missing_required_context
```

This prevents silent merging of multiple packet/cell contexts into one config.

## Value Conversion

Supported value forms:

```text
int
"10"
"0x1f"
"0b1010"
```

The existing text parser already converts SystemVerilog literals in text input
such as:

```text
'h0
8'hff
```

before this adapter sees them. Pre-rendered JSON that still contains raw
SystemVerilog literal strings is reported as:

```text
code: unsupported_format
```

After conversion, the adapter checks unsigned width:

```text
0 <= value <= (2 ** field.width) - 1
```

Overflow is reported as:

```text
code: range_error
```

## Reserved And Payload Handling

Reserved fields are skipped by default:

```text
skipped_reserved_count += 1
```

They do not enter `UserConfig` values.

Payload placeholders and dynamic-array payload nodes are also skipped:

```text
skipped_payload_count += 1
```

This adapter does not convert payload spans into `payload_by_packet`. That
remains a runtime/io integration task.

## Report Model

The report is deterministic and includes:

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

Errors are structured by `code` so later callers can decide whether a condition
is fatal, recoverable, or ignorable.

Current error codes include:

```text
unknown_field
ambiguous_field
missing_value
unsupported_format
type_error
range_error
missing_required_context
```

## Tests Added

Focused tests live in:

```text
tests/test_utils/test_uvm_table_config_adapter.py
```

Coverage includes:

```text
single packet/cell binding to UserConfig and CellConfig.parameters
stable matching for duplicate raw names
ambiguous raw-name failure
reserved field skipping
payload skipping
decimal/hex/binary value conversion
width overflow reporting
default packet/cell index policy
missing context reporting for repeated roots
CLI generation
generated demo file determinism
```

## Extension Points

### 1. Parser Context Metadata

The adapter already recognizes optional:

```text
packet_index
cell_index
```

on root or nested parser JSON nodes.

Future parser work can emit these fields without changing the binding API. The
adapter will propagate node-level context to children.

### 2. Multi-Packet / Multi-Cell Grouping

Current behavior is conservative:

```text
single default packet/cell context unless explicit context metadata exists
```

Future work can add support for parser-emitted group markers such as:

```text
packet0
cell0
cc0
```

The right extension point is context extraction before `_walk_nodes()` calls
`_bind_leaf()`. Avoid adding this logic to schema matching.

### 3. Value Format Plugins

Current `_parse_value()` is deliberately small.

Future formats can be added there or split into a small value-converter helper:

```text
SystemVerilog literal strings in pre-rendered JSON
signed values
enum names
array literals
```

Keep conversion errors structured so reports remain machine-readable.

### 4. Reserved Bit Policy

Current policy skips reserved fields.

Future policies can include:

```text
skip
check_zero
bind_for_debug_only
```

This should be an explicit option rather than a silent behavior change.

### 5. Payload Boundary

Payload placeholders are currently skipped. Future payload integration should
not put payload spans into normal `UserConfig` field values.

Preferred future boundary:

```text
parser/schema report payload range
  -> io/payload loader or runtime payload adapter
  -> payload_by_packet[packet_index][cell_index]
```

### 6. Packet-Scope Tables

The adapter supports `packet` scope fields. Current demo2 schema is cell-scope.

Future packet-scope fixtures should add tests proving:

```text
packet field -> packets[].values
cell field   -> packets[].cells[].values
```

### 7. Validation Integration

This task smoke-tests `ConfigResolver` and `ResolvedConfig.to_core_config()`.

Future validator integration should be separate and can consume the resolved
config produced by this path. Do not add validator business-rule extraction to
this adapter.

### 8. Runtime Integration

Runtime integration should remain a separate task:

```text
schema
  -> config adapter output
  -> UserConfig
  -> run_case()
```

That work must decide algorithm injection, payload inputs, result policy, and
exit status behavior. This utility should stay reusable without runtime.

## Known Limitations

- No `run_case()` integration.
- No algorithm execution.
- No payload injection.
- No Chinese description parsing.
- No automatic validator business-rule generation.
- No direct support for global-scope values in this adapter.
- Raw SystemVerilog literal strings in pre-rendered JSON are not required by
  this task and are reported as unsupported.
- Multi-context binding requires explicit context metadata; repeated roots
  without indexes are rejected.

## Maintenance Notes

When extending this adapter:

```text
1. Preserve parser reuse; do not duplicate text parsing.
2. Keep schema matching deterministic.
3. Never silently choose between ambiguous schema candidates.
4. Keep reserved and payload behavior explicit.
5. Keep report errors structured and counted.
6. Keep Python 3.6.3 compatibility.
7. Add focused tests before broad integration tests.
```
