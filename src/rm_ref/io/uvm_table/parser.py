"""Formal UVM table-printer parser boundary."""

from __future__ import print_function

import ast
import json
import re
from collections import OrderedDict


JSON_FORMAT = "uvm_table_printer/v1"


class UvmTableParserError(Exception):
    """Raised when UVM table-printer text cannot be parsed."""


def convert_value(raw_value):
    value = raw_value.strip()

    if re.match(r"^[+-]?[0-9]+$", value):
        return int(value, 10)
    if re.match(r"^[+-]?0[xX][0-9a-fA-F_]+$", value):
        return int(value.replace("_", ""), 16)
    if re.match(r"^[+-]?0[bB][01_]+$", value):
        return int(value.replace("_", ""), 2)
    if re.match(r"^[+-]?0[oO][0-7_]+$", value):
        return int(value.replace("_", ""), 8)

    sv_match = re.match(
        r"^(?P<sign>[+-]?)(?P<size>[0-9]+)?'(?P<signed>[sS])?"
        r"(?P<base>[bBoOdDhH])(?P<digits>[0-9a-fA-F_]+)$",
        value,
    )
    if sv_match:
        base = {
            "b": 2,
            "o": 8,
            "d": 10,
            "h": 16,
        }[sv_match.group("base").lower()]
        converted = int(sv_match.group("digits").replace("_", ""), base)
        size_text = sv_match.group("size")
        if sv_match.group("signed") and size_text:
            size = int(size_text, 10)
            sign_bit = 1 << (size - 1)
            if converted & sign_bit:
                converted -= 1 << size
        if sv_match.group("sign") == "-":
            converted = -converted
        return converted

    if len(value) >= 2 and value[0] in ("'", '"') and value[-1] == value[0]:
        try:
            literal = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value
        if isinstance(literal, str):
            return literal

    return value


def _header_columns(line):
    stripped = line.strip()
    if not re.match(r"^Name\s+Type\s+Size\s+Value$", stripped):
        return None
    return (
        line.index("Type"),
        line.index("Size"),
        line.index("Value"),
    )


def _parse_row(line, columns):
    if columns is not None and len(line) > columns[0]:
        type_column, size_column, value_column = columns
        name_field = line[:type_column].rstrip()
        name = name_field.strip()
        field_type = line[type_column:size_column].strip()
        size = line[size_column:value_column].strip()
        value = line[value_column:].strip()
        if (
            re.match(r"^\S+$", name or "")
            and field_type
            and re.match(r"^(?:-|[0-9]+)$", size)
        ):
            indent = len(name_field) - len(name_field.lstrip())
            return indent, name, field_type, size, value

    match = re.match(
        r"^(?P<indent>\s*)(?P<name>\S+)\s{2,}"
        r"(?P<type>\S.*?)\s{2,}(?P<size>\S+)\s{2,}(?P<value>.*?)\s*$",
        line,
    )
    if not match:
        return None
    if not re.match(r"^(?:-|[0-9]+)$", match.group("size")):
        return None
    return (
        len(match.group("indent")),
        match.group("name"),
        match.group("type"),
        match.group("size"),
        match.group("value"),
    )


def _iter_table_rows(text):
    columns = None
    for line in text.splitlines():
        detected_columns = _header_columns(line)
        if detected_columns is not None:
            columns = detected_columns
            yield None
            continue

        stripped = line.strip()
        if not stripped or set(stripped) <= set("-="):
            continue

        row = _parse_row(line, columns)
        if row is not None:
            yield row


def _parse_size(raw_size):
    if raw_size == "-":
        return None
    return int(raw_size, 10)


def _new_tree_node(name, field_type, raw_size, raw_value):
    return {
        "name": name,
        "type": field_type,
        "size": _parse_size(raw_size),
        "_raw_value": raw_value,
        "_is_reference": raw_value.startswith("@"),
        "_children": [],
    }


def _finalize_tree_node(node):
    result = OrderedDict()
    result["name"] = node["name"]
    result["type"] = node["type"]
    result["size"] = node["size"]

    children = node["_children"]
    if node["_is_reference"] or children:
        result["children"] = [_finalize_tree_node(child) for child in children]
    else:
        result["value"] = convert_value(node["_raw_value"])
    return result


def parse_uvm_table_tree(text):
    """Return hierarchical UVM table nodes in source order."""
    if not isinstance(text, str):
        raise UvmTableParserError("text must be str")

    roots = []
    hierarchy = []
    for row in _iter_table_rows(text):
        if row is None:
            hierarchy = []
            continue

        indent, name, field_type, raw_size, raw_value = row
        node = _new_tree_node(name, field_type, raw_size, raw_value)

        while hierarchy and hierarchy[-1][0] >= indent:
            hierarchy.pop()
        if hierarchy:
            hierarchy[-1][1]["_children"].append(node)
        else:
            roots.append(node)
        hierarchy.append((indent, node))

    if not roots:
        raise UvmTableParserError("no UVM table rows found")
    return [_finalize_tree_node(root) for root in roots]


def render_uvm_table_json(roots):
    document = OrderedDict()
    document["format"] = JSON_FORMAT
    document["roots"] = roots
    return json.dumps(document, indent=2, ensure_ascii=True) + "\n"
