from rm_ref.validator.result import ERROR, ValidationIssue


def _location(schema_id, packet_index, cell_index):
    parts = ["schema {0}".format(schema_id)]
    if packet_index is not None:
        parts.append("packet {0}".format(packet_index))
    if cell_index is not None:
        parts.append("cell {0}".format(cell_index))
    return " ".join(parts)


def _issue(
    code,
    field,
    schema_id,
    value,
    expected_rule,
    packet_index=None,
    cell_index=None,
    detail=None,
):
    location = _location(schema_id, packet_index, cell_index)
    if detail is None:
        detail = "violates {0}".format(expected_rule)
    message = "{0} field {1} value={2!r} {3}".format(
        location,
        field.normalized_name,
        value,
        detail,
    )
    return ValidationIssue(
        code=code,
        message=message,
        severity=ERROR,
        schema_id=schema_id,
        field_name=field.normalized_name,
        original_field_name=field.original_name,
        packet_index=packet_index,
        cell_index=cell_index,
        value=value,
        expected_rule=expected_rule,
        word=field.word,
        msb=field.msb,
        lsb=field.lsb,
        width=field.width,
        description=field.description,
    )


def validate_mapping(
    values,
    fields,
    schema_id,
    result,
    packet_index=None,
    cell_index=None,
):
    known_names = set(field.normalized_name for field in fields)
    for name, value in values.items():
        if name not in known_names:
            result.add_error(
                ValidationIssue(
                    code="UNKNOWN_FIELD",
                    message=(
                        "{0} contains unknown resolved field {1!r} value={2!r}"
                    ).format(
                        _location(schema_id, packet_index, cell_index),
                        name,
                        value,
                    ),
                    schema_id=schema_id,
                    field_name=name,
                    packet_index=packet_index,
                    cell_index=cell_index,
                    value=value,
                    expected_rule="field must exist in schema at this scope",
                )
            )

    for field in fields:
        if field.reserved:
            continue
        present = field.normalized_name in values
        value = values.get(field.normalized_name)
        if field.required and (not present or value is None):
            result.add_error(
                _issue(
                    "REQUIRED",
                    field,
                    schema_id,
                    value,
                    "required field must be present",
                    packet_index=packet_index,
                    cell_index=cell_index,
                    detail="is required",
                )
            )
            continue
        if not present or value is None:
            continue

        needs_integer = (
            field.width is not None
            or field.min is not None
            or field.max is not None
            or bool(field.enum)
        )
        if needs_integer and (
            isinstance(value, bool) or not isinstance(value, int)
        ):
            result.add_error(
                _issue(
                    "INTEGER_TYPE",
                    field,
                    schema_id,
                    value,
                    "value must be an integer",
                    packet_index=packet_index,
                    cell_index=cell_index,
                )
            )
            continue

        if field.min is not None and value < field.min:
            result.add_error(
                _issue(
                    "MIN_VALUE",
                    field,
                    schema_id,
                    value,
                    "value >= {0}".format(field.min),
                    packet_index=packet_index,
                    cell_index=cell_index,
                )
            )
        if field.max is not None and value > field.max:
            result.add_error(
                _issue(
                    "MAX_VALUE",
                    field,
                    schema_id,
                    value,
                    "value <= {0}".format(field.max),
                    packet_index=packet_index,
                    cell_index=cell_index,
                )
            )
        if field.enum and value not in field.enum_values():
            result.add_error(
                _issue(
                    "ENUM_VALUE",
                    field,
                    schema_id,
                    value,
                    "value in {0}".format(sorted(field.enum_values())),
                    packet_index=packet_index,
                    cell_index=cell_index,
                )
            )
        if field.width is not None:
            maximum = (1 << field.width) - 1
            if value < 0 or value > maximum:
                result.add_error(
                    _issue(
                        "BIT_WIDTH",
                        field,
                        schema_id,
                        value,
                        "unsigned {0}-bit value in [0, {1}]".format(
                            field.width, maximum
                        ),
                        packet_index=packet_index,
                        cell_index=cell_index,
                    )
                )
