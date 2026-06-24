import json
from copy import deepcopy
from pathlib import Path

from rm_ref.config import ConfigResolver, UserConfig
from rm_ref.schema import SchemaDefinition
from utils.parse_uvm_table_print import parse_uvm_table_tree
from utils.uvm_table_config_adapter import (
    bind_config_from_uvm_table_json,
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
SCHEMA_PATH = REPO_ROOT / "schema_defs" / "uvm_table" / "demo2_schema.json"
GENERATED_CONFIG_PATH = (
    REPO_ROOT / "schema_defs" / "uvm_table" / "demo2_rm_user_config.json"
)
GENERATED_REPORT_PATH = (
    REPO_ROOT / "schema_defs" / "uvm_table" / "demo2_config_adapter_report.json"
)


def _document_from_fixture():
    roots = parse_uvm_table_tree(FIXTURE_PATH.read_text(encoding="utf-8"))
    return {"format": "uvm_table_printer/v1", "roots": roots}


def _schema_dict():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _schema():
    return SchemaDefinition.from_dict(_schema_dict())


def _bind_fixture(**kwargs):
    return bind_config_from_uvm_table_json(
        _document_from_fixture(),
        _schema(),
        **kwargs
    )


def _walk_nodes(nodes):
    for node in nodes:
        yield node
        for child in _walk_nodes(node.get("children") or []):
            yield child


def _set_leaf_value(document, name, field_type, value):
    for root in document["roots"]:
        for node in _walk_nodes([root]):
            if node.get("name") == name and node.get("type") == field_type:
                node["value"] = value
                return
    raise AssertionError("field not found: {0} {1}".format(name, field_type))


def _minimal_schema(fields):
    return SchemaDefinition.from_dict(
        {
            "schema_id": "minimal/schema/v1",
            "word_width": 32,
            "word_count": 1,
            "fields": fields,
        }
    )


def _minimal_document(children):
    return {
        "format": "uvm_table_printer/v1",
        "roots": [
            {
                "name": "demo",
                "type": "interface_table",
                "size": None,
                "children": [
                    {
                        "name": "header0",
                        "type": "header_t",
                        "size": None,
                        "children": children,
                    }
                ],
            }
        ],
    }


def test_uvm_json_values_to_rm_config_single_packet_single_cell():
    result = _bind_fixture()

    config = result.config_dict
    assert config["schema_id"] == "demo2/schema/v1"
    assert config["packets"][0]["packet_index"] == 0
    assert config["packets"][0]["cells"][0]["cell_index"] == 0

    user_config = UserConfig.from_dict(config)
    resolved = ConfigResolver().resolve(user_config, schema=_schema())
    core_config = resolved.to_core_config()
    cell_parameters = core_config.packets[0].cells[0].parameters

    assert cell_parameters["cell.header0.packet_type_w0_b31_28"] == 0
    assert cell_parameters["cell.header1.bsrs_w8_b1_0"] == 0
    assert result.report["input_field_count"] == 56
    assert result.report["bound_field_count"] == 46


def test_duplicate_raw_name_requires_stable_schema_match():
    document = _document_from_fixture()
    _set_leaf_value(document, "FreqDomainPos", "integral[31:23]", 3)
    # Set the second duplicate directly after the first has been changed.
    seen = 0
    for root in document["roots"]:
        for node in _walk_nodes([root]):
            if node.get("name") == "FreqDomainPos":
                seen += 1
                if seen == 2:
                    node["value"] = 4

    result = bind_config_from_uvm_table_json(document, _schema())
    values = result.config_dict["packets"][0]["cells"][0]["values"]

    assert values["cell.header0.freqdomainpos_w1_b31_23"] == 3
    assert values["cell.header1.freqdomainpos_w5_b31_23"] == 4
    assert result.report["ambiguous_field_count"] == 0


def test_ambiguous_raw_name_fails_or_reports_error():
    document = {
        "format": "uvm_table_printer/v1",
        "roots": [
            {
                "name": "demo2",
                "type": "interface_table",
                "size": None,
                "children": [
                    {
                        "name": "FreqDomainPos",
                        "type": "integral",
                        "size": 9,
                        "value": 1,
                    }
                ],
            }
        ],
    }

    result = bind_config_from_uvm_table_json(document, _schema())

    assert result.has_errors
    assert result.report["ambiguous_field_count"] == 1
    assert result.report["errors"][0]["code"] == "ambiguous_field"


def test_reserved_field_is_skipped_from_user_config():
    result = _bind_fixture()
    values = result.config_dict["packets"][0]["cells"][0]["values"]

    assert result.report["skipped_reserved_count"] == 10
    assert not any("rsv" in name for name in values)


def test_payload_range_is_not_bound_to_cell_config():
    document = _minimal_document(
        [
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
        ]
    )
    schema = _minimal_schema([])

    result = bind_config_from_uvm_table_json(
        document,
        schema,
        scope_rules={"demo": "cell"},
    )

    assert result.config_dict["packets"] == []
    assert result.report["skipped_payload_count"] == 1
    assert result.report["bound_field_count"] == 0


def test_value_type_conversion_decimal_hex_binary():
    schema = _minimal_schema(
        [
            {
                "name": "cell.a__w0_b3_0",
                "original_name": "a",
                "scope": "cell",
                "word": 0,
                "msb": 3,
                "lsb": 0,
                "width": 4,
            },
            {
                "name": "cell.b__w0_b7_4",
                "original_name": "b",
                "scope": "cell",
                "word": 0,
                "msb": 7,
                "lsb": 4,
                "width": 4,
            },
            {
                "name": "cell.c__w0_b11_8",
                "original_name": "c",
                "scope": "cell",
                "word": 0,
                "msb": 11,
                "lsb": 8,
                "width": 4,
            },
        ]
    )
    document = _minimal_document(
        [
            {"name": "word0", "type": "integral[31:0]", "size": 32, "value": 0},
            {"name": "a", "type": "integral[3:0]", "size": 4, "value": "10"},
            {"name": "b", "type": "integral[7:4]", "size": 4, "value": "0x0f"},
            {"name": "c", "type": "integral[11:8]", "size": 4, "value": "0b1010"},
        ]
    )

    result = bind_config_from_uvm_table_json(
        document,
        schema,
        scope_rules={"demo": "cell"},
    )
    values = result.config_dict["packets"][0]["cells"][0]["values"]

    assert values["cell.a_w0_b3_0"] == 10
    assert values["cell.b_w0_b7_4"] == 15
    assert values["cell.c_w0_b11_8"] == 10


def test_value_width_overflow_is_reported():
    schema = _minimal_schema(
        [
            {
                "name": "cell.a__w0_b3_0",
                "original_name": "a",
                "scope": "cell",
                "word": 0,
                "msb": 3,
                "lsb": 0,
                "width": 4,
            }
        ]
    )
    document = _minimal_document(
        [
            {"name": "word0", "type": "integral[31:0]", "size": 32, "value": 0},
            {"name": "a", "type": "integral[3:0]", "size": 4, "value": "16"},
        ]
    )

    result = bind_config_from_uvm_table_json(
        document,
        schema,
        scope_rules={"demo": "cell"},
    )

    assert result.has_errors
    assert result.report["range_error_count"] == 1
    assert result.report["errors"][0]["code"] == "range_error"


def test_default_packet_cell_index_for_single_context():
    result = _bind_fixture(default_packet_index=2, default_cell_index=3)

    assert result.config_dict["packets"][0]["packet_index"] == 2
    assert result.config_dict["packets"][0]["cells"][0]["cell_index"] == 3


def test_missing_context_for_multi_context_is_reported():
    document = _document_from_fixture()
    document["roots"].append(deepcopy(document["roots"][0]))

    result = bind_config_from_uvm_table_json(document, _schema())

    assert result.has_errors
    assert result.report["missing_context_count"] == 1
    assert result.report["errors"][0]["code"] == "missing_required_context"


def test_cli_generates_rm_user_config_and_report(tmp_path):
    config_output = tmp_path / "rm_user_config.json"
    report_output = tmp_path / "report.json"

    result = main(
        [
            "--input",
            str(FIXTURE_PATH),
            "--schema",
            str(SCHEMA_PATH),
            "--scope-rule",
            "demo2=cell",
            "--config-output",
            str(config_output),
            "--report-output",
            str(report_output),
        ]
    )

    assert result == 0
    config = json.loads(config_output.read_text(encoding="utf-8"))
    report = json.loads(report_output.read_text(encoding="utf-8"))
    assert config["packets"][0]["cells"][0]["values"][
        "cell.header0.packet_type_w0_b31_28"
    ] == 0
    assert report["bound_field_count"] == 46


def test_committed_config_and_report_match_current_generator():
    result = _bind_fixture()

    assert GENERATED_CONFIG_PATH.read_text(encoding="utf-8") == render_json(
        result.config_dict
    )
    assert GENERATED_REPORT_PATH.read_text(encoding="utf-8") == render_json(
        result.report
    )
