import importlib.util
from pathlib import Path

import pytest

from utils.parse_uvm_table_print import (
    GENERATED_HEADER,
    UvmTableParserError,
    apply_mapping,
    convert_value,
    load_mapping_file,
    main,
    parse_uvm_table_text,
    render_python_para_get,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "uvm_table_print"
    / "demo_packet_param_table.txt"
)
MAPPING_PATH = REPO_ROOT / "schema_defs" / "uvm_table" / "demo_mapping.py"
GENERATED_DEMO_PATH = (
    REPO_ROOT / "schema_defs" / "uvm_table" / "demo_generated_para.py"
)


def test_parse_simple_name_value_line():
    text = (
        "Name                         Type                Size    Value\n"
        "field_a                      integral            32      10\n"
    )

    assert parse_uvm_table_text(text) == [("field_a", 10)]


def test_parse_hierarchical_paths_from_fixture():
    parsed = dict(parse_uvm_table_text(FIXTURE_PATH.read_text(encoding="utf-8")))

    assert parsed["packet_param.header0.packet_type"] == 0
    assert parsed["packet_param.header1.packet_type"] == 0
    assert parsed["packet_param.header0.word3"] == 0
    assert parsed["packet_param.word4"] == 0
    assert "packet_param.Payload" not in parsed


def test_ignore_table_border_lines():
    text = (
        "----------------------------------------\n"
        "Name      Type      Size    Value\n"
        "----------------------------------------\n"
        "\n"
    )

    assert parse_uvm_table_text(text) == []


def test_ignore_unsupported_log_line_after_table():
    text = (
        "Name                         Type                Size    Value\n"
        "field_a                      integral            32      10\n"
        "UVM_INFO this is a long log message outside the table output\n"
    )

    assert parse_uvm_table_text(text) == [("field_a", 10)]


@pytest.mark.parametrize(
    "raw_value, expected",
    [
        ("10", 10),
        ("0x10", 16),
        ("0b1010", 10),
        ("-7", -7),
        ("'h10", 16),
        ("8'shff", -1),
        ('"hello"', "hello"),
        ("plain_text", "plain_text"),
    ],
)
def test_convert_supported_values(raw_value, expected):
    assert convert_value(raw_value) == expected


def test_apply_mapping_prefers_full_hierarchical_path():
    parsed = [
        ("packet.header0.packet_type", 1),
        ("packet.header1.packet_type", 2),
    ]
    name_map = {
        "packet.header0.packet_type": "first_type",
        "packet.header1.packet_type": "second_type",
        "packet_type": "fallback_type",
    }

    assert apply_mapping(parsed, name_map) == [
        ("first_type", 1),
        ("second_type", 2),
    ]


def test_apply_mapping_accepts_leaf_name_mapping():
    parsed = [("packet.header.StartSymbol", 3)]

    assert apply_mapping(parsed, {"StartSymbol": "start_symbol"}) == [
        ("start_symbol", 3)
    ]


def test_keep_unmapped_uses_leaf_name():
    assert apply_mapping([("packet.field_a", 4)], {}, keep_unmapped=True) == [
        ("field_a", 4)
    ]


def test_ignore_unmapped():
    assert apply_mapping([("packet.field_a", 4)], {}, keep_unmapped=False) == []


def test_duplicate_rm_parameter_name_is_rejected():
    parsed = [
        ("packet.header0.packet_type", 1),
        ("packet.header1.packet_type", 2),
    ]

    with pytest.raises(UvmTableParserError, match="duplicate RM parameter name"):
        apply_mapping(parsed, {}, keep_unmapped=True)


def test_invalid_rm_parameter_name_is_rejected():
    with pytest.raises(UvmTableParserError, match="Python identifier"):
        apply_mapping([("packet.field", 1)], {"field": "not-valid"})


def test_render_python_para_get():
    rendered = render_python_para_get(
        [("freq_domain_position", 10), ("label", "demo")]
    )

    assert rendered == (
        GENERATED_HEADER
        + "\n\n"
        + "def para_get(parse):\n"
        + "    parse.freq_domain_position = 10\n"
        + "    parse.label = 'demo'\n"
    )


def test_render_empty_python_para_get_uses_pass():
    assert render_python_para_get([]).endswith("def para_get(parse):\n    pass\n")


def test_load_mapping_file():
    name_map, keep_unmapped = load_mapping_file(str(MAPPING_PATH))

    assert name_map["packet_param.header0.packet_type"] == "header0_packet_type"
    assert keep_unmapped is False


def test_cli_generates_importable_output_file(tmp_path):
    output_path = tmp_path / "generated_para.py"

    result = main(
        [
            "--input",
            str(FIXTURE_PATH),
            "--mapping",
            str(MAPPING_PATH),
            "--output",
            str(output_path),
        ]
    )

    assert result == 0
    generated = output_path.read_text(encoding="utf-8")
    assert "parse.header0_packet_type = 0" in generated
    assert "parse.header1_start_symbol = 0" in generated
    assert "parse.frame_num" not in generated

    spec = importlib.util.spec_from_file_location("generated_para", str(output_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    target = type("Target", (), {})()
    module.para_get(target)
    assert target.header0_packet_type == 0
    assert target.word4 == 0


def test_committed_demo_output_matches_current_generator():
    parsed_items = parse_uvm_table_text(FIXTURE_PATH.read_text(encoding="utf-8"))
    name_map, keep_unmapped = load_mapping_file(str(MAPPING_PATH))
    mapped_items = apply_mapping(parsed_items, name_map, keep_unmapped)

    assert GENERATED_DEMO_PATH.read_text(encoding="utf-8") == (
        render_python_para_get(mapped_items)
    )


def test_cli_does_not_write_output_for_duplicate_names(tmp_path, capsys):
    output_path = tmp_path / "generated_para.py"

    result = main(
        [
            "--input",
            str(FIXTURE_PATH),
            "--output",
            str(output_path),
        ]
    )

    assert result == 1
    assert not output_path.exists()
    assert "duplicate RM parameter name" in capsys.readouterr().err
