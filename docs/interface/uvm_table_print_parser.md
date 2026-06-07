# UVM Table Print Parser

## Purpose

`utils/parse_uvm_table_print.py` converts hierarchical text produced by a UVM
table printer into a Python file containing:

```python
def para_get(parse):
    parse.rm_parameter_name = value
```

The utility is outside the RM runtime core. It has no UVM simulator or external
package dependency.

## Input Assumptions

The parser recognizes tables with `Name`, `Type`, `Size`, and `Value` columns.
Leading spaces in the `Name` column define hierarchy. For example,
`packet_param.header0.packet_type` and
`packet_param.header1.packet_type` remain distinct paths.

It ignores borders, headings, blank lines, unsupported lines, object references
such as `@00000001`, and values shown as `-`.

Implemented value conversions are:

- decimal, hexadecimal, binary, and octal Python integers
- signed decimal integers
- SystemVerilog integer literals such as `'h10`, `8'b1010`, and `8'shff`
- quoted or unquoted simple strings

Values containing unknown-state digits such as `x` or `z` are currently kept as
strings.

## Mapping File

A mapping file is a Python file containing `PARAM_NAME_MAP`. It may also contain
`KEEP_UNMAPPED`.

```python
PARAM_NAME_MAP = {
    "packet_param.header0.packet_type": "header0_packet_type",
    "StartSymbol": "start_symbol",
}

KEEP_UNMAPPED = False
```

Mapping lookup checks the full hierarchical path first, then the path without
its top-level object, then the leaf name. Full paths should be used when leaf
names repeat.

When unmapped values are kept, their leaf names become RM parameter names.
Duplicate final names and names that are not valid Python identifiers are
errors. Use explicit full-path mappings to resolve duplicates.

## CLI Usage

```powershell
python utils/parse_uvm_table_print.py `
  --input tests/fixtures/uvm_table_print/demo_packet_param_table.txt `
  --mapping schema_defs/uvm_table/demo_mapping.py `
  --output schema_defs/uvm_table/demo_generated_para.py
```

The repository commits
`schema_defs/uvm_table/demo_generated_para.py` as the deterministic result of
this example command. A test verifies that the committed result still matches
the parser, fixture, and mapping.

Without `--mapping`, unmapped names are kept by default. Override mapping-file
behavior with:

```powershell
--unmapped keep
--unmapped ignore
```

The command returns a non-zero exit code and does not write an output file when
parsing, mapping, or rendering fails.

## Python API

The main pure helpers are:

```python
parse_uvm_table_text(text)
convert_value(raw_value)
apply_mapping(parsed_items, name_map, keep_unmapped=True)
render_python_para_get(mapped_items)
```

`parse_uvm_table_text` returns ordered `(hierarchical_path, value)` pairs.
Generated assignments preserve this input order.

## Current Limitations

- The first version expects whitespace-aligned UVM table-printer columns.
- It emits flat attributes on the object passed to `para_get`.
- Arrays and names containing characters invalid in Python identifiers require
  explicit mappings.
- Unknown-state integer values are preserved as strings instead of being
  represented with a four-state numeric type.
