# UVM Table Schema Adapter Plan

## Purpose

This document records the agreed direction for the next interface-table schema
adapter task.

The current repository already has:

```text
uvm_table_printer text -> generic JSON / para_get
schema dict -> SchemaDefinition.from_dict()
```

The missing layer is:

```text
generic UVM table JSON / uvm_table_printer parser result
  -> RM schema dict
  -> SchemaDefinition.from_dict()
```

The task should stabilize the schema compilation path from interface bit-table
text into an RM `SchemaDefinition`. It must not connect runtime execution,
generate full `UserConfig`, or inject payload into `run_case()`.

## Source Of Truth

The production input is expected to be `uvm_table_printer`-style text produced
outside this repository.

Excel input is reference material only. For local validation, the Excel file
may be used to generate a simulated `uvm_table_printer` fixture, but core schema
generation logic must not depend on an Excel reader.

Reference file:

```text
doc/ref_docs/interface/demo_interface_table_1.xlsx
```

Important correction:

```text
demo2 is the target table to recognize.
demo2 scope is cell.
```

`demo1` was useful during exploration, but it is not the target table for this
adapter task unless a future scope rule explicitly includes it.

## Recommended Flow

Test fixture generation:

```text
Excel interface table
  -> simulated uvm_table_printer text
```

Formal schema compilation:

```text
uvm_table_printer text
  -> existing parser generic JSON
  -> RM schema dict
  -> SchemaDefinition.from_dict()
```

The adapter should consume the existing parser's generic JSON structure. It
should not reimplement the UVM text parser.

## Proposed Module Boundary

Use the existing UVM table utility area rather than runtime or core:

```text
utils/
schema_defs/uvm_table/
tests/test_utils/
tests/fixtures/uvm_table_print/
docs/interface/
```

Possible modules:

```text
utils/uvm_table_schema_adapter.py
```

If the implementation grows, split helper responsibilities conservatively:

```text
interface_table/
  excel_to_uvm_text.py       # optional fixture generator only
  uvm_json_to_schema.py      # core adapter
  naming.py                  # stable field naming
  scope_rules.py             # source/table -> scope mapping
  report.py                  # conversion report model
```

Do not place this logic in:

```text
src/rm_ref/runtime/
src/rm_ref/core/
```

## Required Input Information

The adapter requires enough layout information to infer fields:

```text
source or table name
field order
word marker / word index
field name
field bit width or bit range
reserved marker
payload range marker, if present
```

If the production text only contains flat field names and values, the adapter
cannot reliably recover `word`, `msb`, and `lsb`.

For the local Excel-derived fixture, the known bit-table layout is:

```text
C..AH columns correspond to bits 31..0
B column is word index
merged cells represent field bit ranges
```

The simulated text fixture must preserve this layout information. A fixture
that keeps only field name and value is not sufficient for schema generation.

## Scope Rules

Scope must be supplied by configuration. The adapter must not silently guess.

For the current target:

```json
{
  "scope_rules": {
    "demo2": "cell"
  }
}
```

If a source/table is missing from `scope_rules`, the adapter should fail or
emit a clear warning according to an explicit policy. It must not silently map
unknown tables to `packet`, `cell`, or `global`.

## Schema Field Output

The output schema dict must use fields accepted by the current
`SchemaDefinition.from_dict()` implementation.

Recommended field shape:

```json
{
  "name": "cell.FreqDomainPos__w3_b14_0",
  "original_name": "FreqDomainPos",
  "scope": "cell",
  "word": 3,
  "msb": 14,
  "lsb": 0,
  "reserved": false
}
```

Do not add unsupported top-level field keys such as `raw_name` unless schema
normalization supports them. Keep extra debug data in schema metadata or in the
conversion report.

## Stable Naming

Duplicate raw field names are expected. Names must be stable and should not
depend on encounter-order suffixes like `_1` or `_2`.

Use a deterministic name derived from scope and bit location:

```text
<scope>.<raw_name>__w<word>_b<msb>_<lsb>
```

Examples:

```text
cell.FreqDomainPos__w3_b14_0
cell.Csrs__w4_b5_0
cell.BSrs__w4_b8_6
```

Preserve the source name through `original_name` or report metadata so later
debugging and business mapping remain possible.

## Reserved Fields

Reserved fields should remain in the generated schema. This keeps the schema
usable for bit-table coverage and later reserved-bit checks.

Future `UserConfig` generation may skip reserved fields. That is not part of
this task.

## Payload Ranges

Payload ranges must not become normal `SchemaDefinition.fields`.

For example, a range like:

```text
word 4-199 Payload
```

should be recorded in report or metadata:

```json
{
  "payload_ranges": [
    {
      "scope": "packet",
      "word_start": 4,
      "word_end": 199,
      "reason": "runtime_payload"
    }
  ]
}
```

The current `SchemaDefinition` field model describes single-word control
fields, not packet payload spans.

## Descriptions And Rule Extraction

Chinese description blocks, enum descriptions, ranges, and dependency notes
should be preserved as raw metadata when available.

Do not attempt strong parsing of Chinese descriptions in this task. Punctuation
and wording are not uniform enough for a reliable first-pass rule extractor.

## Report

Generate a deterministic report, for example `report.json`, with at least:

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

The report is the right place for source metadata, skipped rows, payload spans,
raw description text, and adapter warnings that do not belong in the schema
field model.

## Minimum Tests

Add focused tests under `tests/test_utils/`:

```text
test_parse_simulated_uvm_text_to_json
test_uvm_json_to_schema_dict
test_schema_definition_from_dict
test_duplicate_field_naming_is_stable
test_payload_range_is_not_added_as_normal_field
test_scope_rules_are_required_or_applied
```

The fixture should live under:

```text
tests/fixtures/uvm_table_print/
```

Generated example outputs may live under:

```text
schema_defs/uvm_table/
```

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
```

## Acceptance Criteria

1. A simulated `uvm_table_printer` text fixture exists for the `demo2` table.
2. The text fixture is parsed by the existing parser into generic JSON.
3. The new adapter converts that generic JSON into an RM schema dict.
4. `SchemaDefinition.from_dict(schema_dict)` succeeds.
5. A deterministic report is generated with the required summary fields.
6. Tests cover parsing, schema conversion, stable naming, payload skipping, and
   required scope-rule behavior.

## Current Architecture Assessment

The current architecture supports this task. It should be implemented as an
interface/schema utility layer that composes:

```text
utils.parse_uvm_table_print
rm_ref.schema.SchemaDefinition
```

No core or runtime changes are required.
