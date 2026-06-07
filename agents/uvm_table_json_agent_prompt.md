# UVM Table JSON Agent Prompt

## Role

You are the UVM table JSON agent.

Extend the existing Python 3.6-compatible UVM table-printer utility with a
deterministic hierarchical JSON output format.

Do not implement in `rm_ref_main` or reuse `rm_ref_uvm_parser`.

Before implementation, run:

```powershell
python scripts/agent_workflow.py preflight
```

Stop if preflight reports any error.

## Goal

Support this first-version flow:

```text
uvm_table_printer text
  -> hierarchical parsed nodes
  -> deterministic JSON document
```

Keep the existing flat Python `para_get()` output working unchanged.

## JSON Shape

Use a versioned envelope:

```json
{
  "format": "uvm_table_printer/v1",
  "roots": [
    {
      "name": "packet_param",
      "type": "packet_param",
      "size": null,
      "children": [
        {
          "name": "header0",
          "type": "header_t",
          "size": null,
          "children": [
            {
              "name": "packet_type",
              "type": "integral",
              "size": 4,
              "value": 0
            }
          ]
        }
      ]
    }
  ]
}
```

Each node must preserve:

```text
name
type
size
value for leaf values
children for object nodes
```

Represent UVM object references such as `@00000001` as hierarchy containers,
not as scalar configuration values.

## Required Behavior

1. Add a parser API that returns hierarchical nodes.
2. Reuse the existing value conversion behavior.
3. Add deterministic JSON rendering with two-space indentation and one final
   newline.
4. Add `--format python|json`; keep `python` as the default.
5. Do not change existing Python output for existing commands.
6. Reject input with no supported table nodes.
7. Do not leave partial output files after serious errors.
8. Keep Python 3.6.3 compatibility.
9. Add focused pytest coverage and interface documentation.

## Non-Goals

Do not implement in this task:

```text
multi-file manifests
component-carrier semantics
packet/cell business mapping
payload loading or embedding
UserConfig adapters
RM core, config, validator, packer, or algorithm changes
```

Those require separate tasks after the generic JSON representation is stable.

## Preferred APIs

```python
def parse_uvm_table_tree(text):
    ...

def render_uvm_table_json(roots):
    ...
```

Small helpers or explicit normal classes are acceptable. Do not use
`dataclasses`, `TypedDict`, `Protocol`, `Literal`, built-in generic syntax,
union `|`, or other Python 3.7+ features.

## CLI

Existing behavior remains valid:

```powershell
python utils/parse_uvm_table_print.py `
  --input input.txt `
  --mapping mapping.py `
  --output generated_para.py
```

JSON output:

```powershell
python utils/parse_uvm_table_print.py `
  --input input.txt `
  --format json `
  --output generated_table.json
```

Mapping is part of the Python output path. The first JSON version should
faithfully preserve source hierarchy and names rather than flattening them.

## Tests

Cover at least:

```text
single leaf node
nested object hierarchy
type and size preservation
decimal, hex, binary, signed, and string values
object references become containers
JSON round trip with json.loads
deterministic rendering
one final newline
CLI JSON generation
empty/unsupported input failure
existing Python rendering regression
existing Python CLI compatibility
```

Commit one deterministic generated JSON example under
`schema_defs/uvm_table/` and test regeneration against it.

## Documentation

Add or update documentation under `docs/interface/` covering:

```text
implemented JSON format
CLI usage
node fields
value conversion
compatibility with Python output
known limitations
future mapping/adaptation work
```

Do not describe multi-CC or UserConfig adaptation as implemented.

## Completion

Run:

```powershell
python -m pytest -q tests/test_utils
python utils/parse_uvm_table_print.py --help
python scripts/agent_workflow.py check-scope
git status --short
```

Run `python -m pytest -q` when reasonable.

Report files changed, API and CLI changes, tests, failures, limitations, and
follow-up. Do not update shared workflow status or journal files. Do not
commit unless explicitly requested.
