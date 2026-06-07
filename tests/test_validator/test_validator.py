from copy import deepcopy

from rm_ref.config import (
    ResolvedCellConfig,
    ResolvedConfig,
    ResolvedPacketConfig,
)
from rm_ref.schema import SchemaDefinition
from rm_ref.validator import WARNING, ValidationIssue, Validator


def make_schema():
    return SchemaDefinition.from_dict(
        {
            "schema_id": "validate/v1",
            "word_width": 8,
            "word_count": 2,
            "fields": [
                {
                    "name": "packet_kind",
                    "scope": "packet",
                    "required": True,
                    "enum": {"DATA": 1, "CTRL": 2},
                    "word": 0,
                    "msb": 1,
                    "lsb": 0,
                },
                {
                    "name": "gain",
                    "scope": "cell",
                    "required": True,
                    "min": 2,
                    "max": 10,
                    "word": 1,
                    "msb": 3,
                    "lsb": 0,
                    "description": "Cell gain",
                },
                {
                    "name": "small_value",
                    "scope": "cell",
                    "word": 1,
                    "msb": 5,
                    "lsb": 4,
                },
            ],
        }
    )


def make_resolved(packet_values=None, cell_values=None):
    return ResolvedConfig(
        case_name="case",
        algorithm_name="demo",
        schema_id="validate/v1",
        packets=[
            ResolvedPacketConfig(
                packet_index=4,
                values=packet_values or {},
                cells=[
                    ResolvedCellConfig(
                        cell_index=7,
                        values=cell_values or {},
                    )
                ],
            )
        ],
    )


def test_valid_config_returns_ok():
    result = Validator(make_schema()).validate(
        make_resolved(
            packet_values={"packet_kind": 1},
            cell_values={"gain": 5, "small_value": 3},
        )
    )

    assert result.ok
    assert result.errors == []
    assert result.warnings == []


def test_missing_required_reports_full_context():
    result = Validator(make_schema()).validate(make_resolved())

    assert not result.ok
    assert [issue.code for issue in result.errors] == ["REQUIRED", "REQUIRED"]
    packet_error = result.errors[0]
    cell_error = result.errors[1]
    assert packet_error.schema_id == "validate/v1"
    assert packet_error.packet_index == 4
    assert packet_error.field_name == "packet_kind"
    assert cell_error.cell_index == 7
    assert cell_error.original_field_name == "gain"


def test_min_and_max_violations_report_expected_rules():
    low = Validator(make_schema()).validate(
        make_resolved({"packet_kind": 1}, {"gain": 1})
    )
    high = Validator(make_schema()).validate(
        make_resolved({"packet_kind": 1}, {"gain": 11})
    )

    assert low.errors[0].code == "MIN_VALUE"
    assert low.errors[0].expected_rule == "value >= 2"
    assert high.errors[0].code == "MAX_VALUE"
    assert high.errors[0].expected_rule == "value <= 10"


def test_enum_violation_reports_allowed_values():
    result = Validator(make_schema()).validate(
        make_resolved({"packet_kind": 3}, {"gain": 5})
    )

    error = result.errors[0]
    assert error.code == "ENUM_VALUE"
    assert error.value == 3
    assert error.expected_rule == "value in [1, 2]"


def test_bit_width_violation_reports_word_and_bit_metadata():
    result = Validator(make_schema()).validate(
        make_resolved(
            {"packet_kind": 1},
            {"gain": 5, "small_value": 4},
        )
    )

    error = result.errors[0]
    assert error.code == "BIT_WIDTH"
    assert error.word == 1
    assert error.msb == 5
    assert error.lsb == 4
    assert error.width == 2
    assert "unsigned 2-bit" in error.expected_rule


def test_non_integer_and_multiple_errors_are_collected():
    result = Validator(make_schema()).validate(
        make_resolved(
            {"packet_kind": "DATA"},
            {"gain": 20, "small_value": -1},
        )
    )

    assert not result.ok
    assert [issue.code for issue in result.errors] == [
        "INTEGER_TYPE",
        "MAX_VALUE",
        "BIT_WIDTH",
        "BIT_WIDTH",
    ]


def test_custom_rule_can_add_warning_and_return_error():
    def custom_rule(config, schema, result):
        result.add_warning(
            ValidationIssue(
                code="DEFAULT_USED",
                message="default was used",
                severity=WARNING,
                schema_id=schema.schema_id,
            )
        )
        return ValidationIssue(
            code="CROSS_FIELD",
            message="cross-field constraint failed",
            schema_id=schema.schema_id,
            rule_name="packet_cell_match",
            expected_rule="packet and cell values must match",
        )

    validator = Validator(make_schema()).add_rule(custom_rule)
    result = validator.validate(
        make_resolved({"packet_kind": 1}, {"gain": 5})
    )

    assert not result.ok
    assert result.errors[0].code == "CROSS_FIELD"
    assert result.errors[0].rule_name == "packet_cell_match"
    assert result.warnings[0].code == "DEFAULT_USED"


def test_validator_does_not_mutate_resolved_config():
    resolved = make_resolved(
        {"packet_kind": 1},
        {"gain": 5, "small_value": 2},
    )
    original = deepcopy(resolved)

    Validator(make_schema()).validate(resolved)

    assert resolved.packets[0].values == original.packets[0].values
    assert resolved.packets[0].cells[0].values == (
        original.packets[0].cells[0].values
    )
