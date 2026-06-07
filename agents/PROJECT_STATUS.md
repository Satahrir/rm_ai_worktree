# Agent Project Status

## Current project state

This repository is a clean Python 3.6-compatible RM Reference Model rebuild.

The main branch has already gone through these stages:

```text
1. Multi-level AGENTS.md files were added.
2. Agent prompts were added under agents/.
3. Core Agent was executed.
4. Tests Agent was executed.
5. Core and tests were merged, with conflicts resolved.
6. Config Agent was merged.
7. Schema/config/validator flow is now part of the project.
```

## Important current focus

The current active feature is:

```text
UVM table printer parser utility
```

This feature is a utility feature.

It must not modify RM core.

## Relevant files

Raw reference files:

```text
doc/ref_docs/interface/demo_interface_table.xlsx
doc/ref_docs/interface/uvm_table_print_demo.txt
```

Test fixture:

```text
tests/fixtures/uvm_table_print/demo_packet_param_table.txt
```

Parser design document:

```text
docs/interface/uvm_table_print_parser.md
```

Parser prompt:

```text
agents/uvm_table_parser_agent_prompt.md
```

Target parser implementation:

```text
utils/parse_uvm_table_print.py
```

Target mapping file:

```text
schema_defs/uvm_table/demo_packet_param_mapping.py
```

Target tests:

```text
tests/test_utils/test_parse_uvm_table_print.py
```

## UVM table format

The current UVM table printer example is hierarchical.

It contains a structure like:

```text
packet_param
  header0
    word0
    packet_type
    fpga_link_id
    frame_num
    slot_num
  header1
    word0
    packet_type
    fpga_link_id
    frame_num
    slot_num
  word4
  Payload
```

Repeated names under different parents must remain distinct.

Correct examples:

```text
packet_param.header0.packet_type
packet_param.header1.packet_type
```

Incorrect behavior:

```text
packet_type
```

The parser must preserve hierarchy.

## Current parser goal

The parser should implement this flow:

```text
uvm_table_printer txt
  -> hierarchical parameter paths
  -> value conversion
  -> optional mapping
  -> generated para_get(parse) Python file
```

The generated file should contain:

```python
def para_get(parse):
    parse.<rm_para_name> = <para_value>
```

## Current restrictions

The UVM table parser must not modify:

```text
src/rm_ref/core/
src/rm_ref/config/
src/rm_ref/validator/
src/rm_ref/packer/
src/rm_ref/algorithms/
```

It may modify:

```text
utils/
schema_defs/uvm_table/
tests/test_utils/
tests/fixtures/uvm_table_print/
docs/interface/
```

## General agent rules

Before starting any task, read:

```text
AGENTS.md
agents/README.md
docs/architecture/98_project_progress_snapshot.md
docs/architecture/99_multi_agent_workflow.md
```

Then read your role-specific prompt under:

```text
agents/
```

Do not commit automatically.

At the end, report:

```text
files changed
tests run
current failures
known limitations
follow-up needed
```