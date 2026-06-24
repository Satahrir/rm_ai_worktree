import json
from pathlib import Path

import pytest

from rm_ref.schema import SchemaDefinition
from utils.parse_uvm_table_print import parse_uvm_table_tree
from utils.uvm_table_schema_adapter import (
    UvmTableSchemaAdapterError,
    compile_schema_from_uvm_table_json,
    main,
    render_json,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "uvm_table_print"
    / "demo2_schema_input_candidate.txt"
)
GENERATED_SCHEMA_PATH = (
    REPO_ROOT / "schema_defs" / "uvm_table" / "demo2_schema.json"
)
GENERATED_REPORT_PATH = (
    REPO_ROOT / "schema_defs" / "uvm_table" / "demo2_schema_report.json"
)


def _document_from_fixture():
    roots = parse_uvm_table_tree(FIXTURE_PATH.read_text(encoding="utf-8"))
    return {"format": "uvm_table_printer/v1", "roots": roots}


def _compile_fixture():
    return compile_schema_from_uvm_table_json(
        _document_from_fixture(),
        schema_id="demo2/schema/v1",
        scope_rules={"demo2": "cell"},
    )


def test_parse_simulated_uvm_text_to_json():
    document = _document_from_fixture()

    assert document["format"] == "uvm_table_printer/v1"
    assert document["roots"][0]["name"] == "demo2"
    header0 = document["roots"][0]["children"][0]["children"][0]
    assert header0["name"] == "header0"
    assert header0["children"][1]["name"] == "packet_type"
    assert header0["children"][1]["type"] == "integral[31:28]"


def test_uvm_json_to_schema_dict():
    result = _compile_fixture()
    schema = result.schema_dict

    assert schema["schema_id"] == "demo2/schema/v1"
    assert schema["word_width"] == 32
    assert schema["word_count"] == 9
    assert len(schema["fields"]) == 56
    first = schema["fields"][0]
    assert first == {
        "name": "cell.header0.packet_type__w0_b31_28",
        "original_name": "packet_type",
        "scope": "cell",
        "word": 0,
        "msb": 31,
        "lsb": 28,
        "width": 4,
        "reserved": False,
    }


def test_schema_definition_from_dict():
    result = _compile_fixture()

    schema = SchemaDefinition.from_dict(result.schema_dict)

    assert schema.schema_id == "demo2/schema/v1"
    assert schema.word_width == 32
    assert schema.word_count == 9
    assert schema.require_field("cell.header0.packet_type__w0_b31_28").width == 4


def test_duplicate_field_naming_is_stable():
    fields = _compile_fixture().schema_dict["fields"]
    names = [field["name"] for field in fields]

    assert "cell.header0.FreqDomainPos__w1_b31_23" in names
    assert "cell.header1.FreqDomainPos__w5_b31_23" in names
    assert len(names) == len(set(names))


def test_word_markers_are_not_added_as_fields():
    fields = _compile_fixture().schema_dict["fields"]

    assert not any(field["original_name"].startswith("word") for field in fields)


def test_reserved_fields_are_kept():
    fields = _compile_fixture().schema_dict["fields"]
    reserved = [field for field in fields if field["reserved"]]

    assert len(reserved) == 10
    assert "cell.header0.RSV_word1_b11__w1_b11_11" in [
        field["name"] for field in reserved
    ]
    assert _compile_fixture().report["reserved_count"] == 10


def test_payload_range_is_not_added_as_normal_field():
    document = {
        "format": "uvm_table_printer/v1",
        "roots": [
            {
                "name": "demo2",
                "type": "interface_table",
                "size": None,
                "children": [
                    {
                        "name": "header0",
                        "type": "header_t",
                        "size": None,
                        "children": [
                            {
                                "name": "word0",
                                "type": "integral[31:0]",
                                "size": 32,
                                "value": 0,
                            },
                            {
                                "name": "Payload",
                                "type": "da(integral)",
                                "size": None,
                                "value": "-",
                            },
                        ],
                    }
                ],
            }
        ],
    }

    result = compile_schema_from_uvm_table_json(
        document,
        schema_id="payload/schema/v1",
        scope_rules={"demo2": "cell"},
    )

    assert result.schema_dict["fields"] == []
    assert result.report["payload_range_count"] == 1
    assert result.report["skipped_field_count"] == 1
    assert result.report["payload_ranges"][0]["name"] == "Payload"


def test_scope_rules_are_required_or_applied():
    document = _document_from_fixture()

    with pytest.raises(UvmTableSchemaAdapterError, match="no scope rule"):
        compile_schema_from_uvm_table_json(
            document,
            schema_id="missing/scope/v1",
            scope_rules={"other": "cell"},
        )

    result = compile_schema_from_uvm_table_json(
        document,
        schema_id="demo2/schema/v1",
        scope_rules={"demo2": "cell"},
    )
    assert set(field["scope"] for field in result.schema_dict["fields"]) == set(
        ["cell"]
    )


def test_report_contains_summary_counts():
    report = _compile_fixture().report

    assert report["schema_id"] == "demo2/schema/v1"
    assert report["word_width"] == 32
    assert report["word_count"] == 9
    assert report["field_count"] == 56
    assert report["reserved_count"] == 10
    assert report["duplicate_raw_name_count"] == 21
    assert report["payload_range_count"] == 0
    assert report["skipped_field_count"] == 0
    assert report["warnings"] == []


def test_cli_generates_schema_and_report(tmp_path):
    schema_output = tmp_path / "schema.json"
    report_output = tmp_path / "report.json"

    result = main(
        [
            "--input",
            str(FIXTURE_PATH),
            "--schema-id",
            "demo2/schema/v1",
            "--scope-rule",
            "demo2=cell",
            "--schema-output",
            str(schema_output),
            "--report-output",
            str(report_output),
        ]
    )

    assert result == 0
    schema = json.loads(schema_output.read_text(encoding="utf-8"))
    report = json.loads(report_output.read_text(encoding="utf-8"))
    assert schema["fields"][0]["name"] == "cell.header0.packet_type__w0_b31_28"
    assert report["field_count"] == 56


def test_committed_schema_and_report_match_current_generator():
    result = _compile_fixture()

    assert GENERATED_SCHEMA_PATH.read_text(encoding="utf-8") == render_json(
        result.schema_dict
    )
    assert GENERATED_REPORT_PATH.read_text(encoding="utf-8") == render_json(
        result.report
    )
