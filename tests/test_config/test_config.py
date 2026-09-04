from copy import deepcopy

import pytest

from rm_ref.config import (
    ConfigResolutionError,
    ConfigResolver,
    UserCellConfig,
    UserConfig,
    UserPacketConfig,
)
from rm_ref.schema import SchemaDefinition, SchemaRegistry


def make_schema():
    return SchemaDefinition.from_dict(
        {
            "schema_id": "demo/v1",
            "word_width": 16,
            "word_count": 2,
            "fields": [
                {
                    "name": "run_mode",
                    "scope": "global",
                    "enum": {"FAST": 1, "SAFE": 2},
                    "default": "SAFE",
                },
                {
                    "name": "packet_type",
                    "scope": "packet",
                    "enum": {"DATA": 3, "CTRL": 4},
                    "default": "DATA",
                    "word": 0,
                    "msb": 3,
                    "lsb": 0,
                },
                {
                    "name": "Cell Gain",
                    "scope": "cell",
                    "default": 5,
                    "word": 1,
                    "msb": 7,
                    "lsb": 0,
                },
            ],
        }
    )


def test_user_config_constructs_packet_and_cell_from_dicts():
    config = UserConfig.from_dict(
        {
            "case_name": "case-a",
            "algorithm_name": "demo",
            "schema_id": "demo/v1",
            "packets": [
                {
                    "packet_index": 4,
                    "values": {"packet_type": "CTRL"},
                    "cells": [{"cell_index": 7, "values": {"Cell Gain": 9}}],
                }
            ],
        }
    )

    assert isinstance(config.packets[0], UserPacketConfig)
    assert isinstance(config.packets[0].cells[0], UserCellConfig)
    assert config.packets[0].packet_index == 4
    assert config.packets[0].cells[0].cell_index == 7


def test_resolver_uses_registry_and_applies_scope_defaults():
    registry = SchemaRegistry()
    registry.register(make_schema())
    resolver = ConfigResolver(registry)
    resolved = resolver.resolve(
        UserConfig(
            case_name="case-a",
            algorithm_name="demo",
            schema_id="demo/v1",
            packets=[UserPacketConfig(cells=[UserCellConfig()])],
        )
    )

    assert resolved.global_values == {"run_mode": 2}
    assert resolved.global_value_sources == {"run_mode": "schema_default"}
    assert resolved.packets[0].values == {"packet_type": 3}
    assert resolved.packets[0].cells[0].values == {"cell_gain": 5}
    assert resolved.packets[0].packet_index == 0
    assert resolved.packets[0].cells[0].cell_index == 0


def test_resolver_reports_missing_registry_schema_as_config_error():
    with pytest.raises(ConfigResolutionError) as exc_info:
        ConfigResolver(SchemaRegistry()).resolve(
            UserConfig(schema_id="missing/v1")
        )

    assert exc_info.value.schema_id == "missing/v1"
    assert "not registered" in str(exc_info.value)


def test_resolver_converts_enum_name_and_preserves_numeric_value():
    schema = make_schema()
    resolved = ConfigResolver().resolve(
        UserConfig(
            schema_id="demo/v1",
            global_values={"run_mode": "FAST"},
            packets=[
                UserPacketConfig(
                    packet_index=3,
                    values={"packet_type": 4},
                    cells=[UserCellConfig(values={"Cell Gain": 8})],
                )
            ],
        ),
        schema=schema,
    )

    assert resolved.global_values["run_mode"] == 1
    assert resolved.packets[0].values["packet_type"] == 4
    assert resolved.packets[0].cells[0].values["cell_gain"] == 8
    assert resolved.packets[0].value_sources["packet_type"] == "user"


def test_resolver_rejects_unknown_enum_name_with_context():
    schema = make_schema()
    with pytest.raises(ConfigResolutionError) as exc_info:
        ConfigResolver().resolve(
            UserConfig(
                schema_id="demo/v1",
                packets=[
                    UserPacketConfig(
                        packet_index=2,
                        values={"packet_type": "BROKEN"},
                    )
                ],
            ),
            schema=schema,
        )

    error = exc_info.value
    assert error.schema_id == "demo/v1"
    assert error.field_name == "packet_type"
    assert error.packet_index == 2
    assert error.value == "BROKEN"


def test_resolver_rejects_unknown_and_wrong_scope_fields():
    schema = make_schema()
    with pytest.raises(ConfigResolutionError, match="no unambiguous field"):
        ConfigResolver().resolve(
            UserConfig(schema_id="demo/v1", global_values={"missing": 1}),
            schema=schema,
        )
    with pytest.raises(ConfigResolutionError, match="belongs to cell scope"):
        ConfigResolver().resolve(
            UserConfig(schema_id="demo/v1", global_values={"Cell Gain": 1}),
            schema=schema,
        )


def test_resolver_preserves_structure_and_does_not_mutate_user_config():
    schema = make_schema()
    user_config = UserConfig(
        case_name="unchanged",
        schema_id="demo/v1",
        global_values={"run_mode": "FAST"},
        packets=[
            UserPacketConfig(
                packet_index=8,
                values={"packet_type": "CTRL"},
                cells=[
                    UserCellConfig(cell_index=2, values={}),
                    UserCellConfig(cell_index=5, values={"Cell Gain": 12}),
                ],
            )
        ],
    )
    original = deepcopy(user_config)

    resolved = ConfigResolver().resolve(user_config, schema=schema)

    assert resolved.packets[0].packet_index == 8
    assert [cell.cell_index for cell in resolved.packets[0].cells] == [2, 5]
    assert user_config.global_values == original.global_values
    assert user_config.packets[0].values == original.packets[0].values
    assert user_config.packets[0].cells[0].values == {}


def test_resolved_config_converts_to_generic_core_config():
    schema = make_schema()
    resolved = ConfigResolver().resolve(
        UserConfig(
            case_name="core-case",
            algorithm_name="demo",
            schema_id="demo/v1",
            packets=[UserPacketConfig(cells=[UserCellConfig()])],
        ),
        schema=schema,
    )

    core_config = resolved.to_core_config()

    assert core_config.case_name == "core-case"
    assert core_config.global_cfg.parameters["algorithm_name"] == "demo"
    assert core_config.global_cfg.parameters["run_mode"] == 2
    assert core_config.packets[0].parameters["packet_type"] == 3
    assert core_config.packets[0].cells[0].parameters["cell_gain"] == 5


def test_repeated_core_conversion_is_deterministic_and_independent():
    resolved = ConfigResolver().resolve(
        UserConfig(
            case_name="repeatable",
            algorithm_name="demo",
            schema_id="demo/v1",
            packets=[UserPacketConfig(cells=[UserCellConfig()])],
        ),
        schema=make_schema(),
    )

    first = resolved.to_core_config()
    second = resolved.to_core_config()
    first.global_cfg.parameters["run_mode"] = 99
    first.packets[0].parameters["packet_type"] = 99
    first.packets[0].cells[0].parameters["cell_gain"] = 99

    assert first is not second
    assert second.global_cfg.parameters["run_mode"] == 2
    assert second.packets[0].packet_index == 0
    assert second.packets[0].parameters["packet_type"] == 3
    assert second.packets[0].cells[0].cell_index == 0
    assert second.packets[0].cells[0].parameters["cell_gain"] == 5
    assert resolved.global_values["run_mode"] == 2
    assert resolved.packets[0].values["packet_type"] == 3
    assert resolved.packets[0].cells[0].values["cell_gain"] == 5
