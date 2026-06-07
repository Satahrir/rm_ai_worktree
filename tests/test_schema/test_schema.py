import pytest

from rm_ref.schema import (
    DuplicateSchemaError,
    SchemaDefinition,
    SchemaError,
    SchemaNotFoundError,
    SchemaRegistry,
    normalize_field_name,
)


def test_schema_from_dict_normalizes_metadata():
    schema = SchemaDefinition.from_dict(
        {
            "schema_id": "demo/v1",
            "word_width": 32,
            "word_count": 2,
            "owner": "unit-test",
            "fields": [
                {
                    "name": "Packet Type",
                    "word": 0,
                    "msb": 7,
                    "lsb": 4,
                    "enum": {"DATA": 1, "CTRL": 2},
                    "default": "DATA",
                    "description": "Packet selector",
                }
            ],
        }
    )

    field = schema.fields[0]
    assert schema.schema_id == "demo/v1"
    assert schema.metadata == {"owner": "unit-test"}
    assert field.name == "Packet Type"
    assert field.original_name == "Packet Type"
    assert field.normalized_name == "packet_type"
    assert field.width == 4
    assert field.enum == {"DATA": 1, "CTRL": 2}
    assert field.default == "DATA"
    assert field.has_default
    assert field.description == "Packet selector"


def test_normalize_field_name_preserves_namespace_segments():
    assert normalize_field_name("Header 0.Frame-Num") == "header_0.frame_num"


def test_invalid_bit_range_reports_schema_and_field():
    with pytest.raises(SchemaError) as exc_info:
        SchemaDefinition.from_dict(
            {
                "schema_id": "bad/v1",
                "word_width": 8,
                "word_count": 1,
                "fields": [
                    {"name": "gain", "word": 0, "msb": 9, "lsb": 4}
                ],
            }
        )

    message = str(exc_info.value)
    assert "bad/v1" in message
    assert "gain" in message
    assert "msb=9" in message


def test_declared_width_must_match_bit_range():
    with pytest.raises(SchemaError, match="width mismatch"):
        SchemaDefinition.from_dict(
            {
                "schema_id": "bad-width/v1",
                "word_width": 8,
                "word_count": 1,
                "fields": [
                    {
                        "name": "gain",
                        "word": 0,
                        "msb": 3,
                        "lsb": 0,
                        "width": 3,
                    }
                ],
            }
        )


def test_duplicate_original_names_are_disambiguated_by_group():
    schema = SchemaDefinition.from_dict(
        {
            "schema_id": "duplicate/v1",
            "word_width": 16,
            "word_count": 2,
            "fields": [
                {
                    "name": "frame_num",
                    "original_name": "frame_num",
                    "group": "header0",
                    "instance": 0,
                    "word": 0,
                    "msb": 3,
                    "lsb": 0,
                },
                {
                    "name": "frame_num",
                    "original_name": "frame_num",
                    "group": "header1",
                    "instance": 1,
                    "word": 1,
                    "msb": 3,
                    "lsb": 0,
                },
            ],
        }
    )

    assert [field.normalized_name for field in schema.fields] == [
        "header0.frame_num",
        "header1.frame_num",
    ]
    assert schema.get_field("frame_num") is None
    assert schema.get_field("header1.frame_num").instance == 1


def test_duplicate_original_names_are_disambiguated_by_instance():
    schema = SchemaDefinition.from_dict(
        {
            "schema_id": "instances/v1",
            "word_width": 8,
            "word_count": 2,
            "fields": [
                {"name": "flag", "instance": 0, "word": 0, "msb": 0, "lsb": 0},
                {"name": "flag", "instance": 1, "word": 1, "msb": 0, "lsb": 0},
            ],
        }
    )

    assert [field.normalized_name for field in schema.fields] == [
        "flag.instance0",
        "flag.instance1",
    ]


def test_duplicate_normalized_names_are_rejected():
    with pytest.raises(SchemaError, match="duplicate normalized field name"):
        SchemaDefinition.from_dict(
            {
                "schema_id": "duplicate/v1",
                "word_width": 8,
                "word_count": 1,
                "fields": [
                    {"name": "A-B"},
                    {"name": "A B"},
                ],
            }
        )


def test_reserved_field_is_preserved_but_not_required():
    schema = SchemaDefinition.from_dict(
        {
            "schema_id": "reserved/v1",
            "word_width": 8,
            "word_count": 1,
            "fields": [
                {
                    "name": "RSV_0",
                    "word": 0,
                    "msb": 7,
                    "lsb": 4,
                    "required": True,
                }
            ],
        }
    )

    field = schema.fields[0]
    assert field.reserved is True
    assert field.required is False


def test_registry_register_get_has_and_duplicate_policy():
    registry = SchemaRegistry()
    schema = registry.register(
        {
            "schema_id": "demo/v1",
            "word_width": 8,
            "word_count": 1,
            "fields": [],
        }
    )

    assert registry.has("demo/v1")
    assert registry.get("demo/v1") is schema
    assert registry.schema_ids() == ["demo/v1"]
    with pytest.raises(DuplicateSchemaError):
        registry.register(schema)
    with pytest.raises(SchemaNotFoundError):
        registry.get("missing/v1")
