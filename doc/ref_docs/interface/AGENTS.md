# Interface Reference Rules

Files in this directory are read-only reference inputs unless the user
explicitly requests an update.

They may be used by utilities and tests to understand external interface
formats. Runtime RM packages must not import or depend on these files.

For the UVM table parser:

- `uvm_table_print_demo.txt` is a parser reference input.
- `demo_interface_table.xlsx` is reference material only in the first parser
  version.
- Do not modify either source file while implementing the parser.
- Copy small stable examples into `tests/fixtures/` when a test fixture is
  needed.
