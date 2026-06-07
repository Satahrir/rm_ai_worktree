import importlib.util
import json
from pathlib import Path

import pytest

import utils.parse_uvm_table_print as parser_module
from utils.parse_uvm_table_print import (
    GENERATED_HEADER,
    JSON_FORMAT,
    UvmTableParserError,
    apply_mapping,
    convert_value,
    load_mapping_file,
    main,
    parse_uvm_table_text,
    parse_uvm_table_tree,
    render_python_para_get,
    render_uvm_table_json,
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
GENERATED_JSON_DEMO_PATH = (
    REPO_ROOT / "schema_defs" / "uvm_table" / "demo_generated_table.json"
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


def test_parse_tree_single_leaf_preserves_type_size_and_value():
    text = (
        "Name                         Type                Size    Value\n"
        "field_a                      integral            32      10\n"
    )

    assert parse_uvm_table_tree(text) == [
        {
            "name": "field_a",
            "type": "integral",
            "size": 32,
            "value": 10,
        }
    ]


def test_parse_tree_builds_nested_object_reference_containers():
    text = (
        "Name                         Type                Size    Value\n"
        "packet                       packet_t            -       @00000001\n"
        "  header                     header_t            -       @00000002\n"
        "    packet_type              integral            4       'h3\n"
    )

    roots = parse_uvm_table_tree(text)

    assert roots == [
        {
            "name": "packet",
            "type": "packet_t",
            "size": None,
            "children": [
                {
                    "name": "header",
                    "type": "header_t",
                    "size": None,
                    "children": [
                        {
                            "name": "packet_type",
                            "type": "integral",
                            "size": 4,
                            "value": 3,
                        }
                    ],
                }
            ],
        }
    ]
    assert "value" not in roots[0]
    assert "value" not in roots[0]["children"][0]


@pytest.mark.parametrize(
    "raw_value, expected",
    [
        ("10", 10),
        ("0x10", 16),
        ("0b1010", 10),
        ("-7", -7),
        ("8'shff", -1),
        ('"hello"', "hello"),
    ],
)
def test_parse_tree_reuses_value_conversion(raw_value, expected):
    text = (
        "Name                         Type                Size    Value\n"
        "field_a                      integral            32      {0}\n".format(
            raw_value
        )
    )

    assert parse_uvm_table_tree(text)[0]["value"] == expected


def test_object_reference_without_children_is_still_a_container():
    text = (
        "Name                         Type                Size    Value\n"
        "empty_object                 object_t            -       @00000001\n"
    )

    assert parse_uvm_table_tree(text) == [
        {
            "name": "empty_object",
            "type": "object_t",
            "size": None,
            "children": [],
        }
    ]


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


def test_render_uvm_table_json_is_deterministic_and_round_trips():
    roots = [
        {
            "name": "field_a",
            "type": "integral",
            "size": 32,
            "value": 10,
        }
    ]

    first = render_uvm_table_json(roots)
    second = render_uvm_table_json(roots)

    assert first == second
    assert first.endswith("\n")
    assert not first.endswith("\n\n")
    assert first.startswith('{\n  "format": "uvm_table_printer/v1",\n')
    assert json.loads(first) == {"format": JSON_FORMAT, "roots": roots}


def test_cli_argument_error_prints_complete_help(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code == 2
    error_output = capsys.readouterr().err
    assert "usage: " in error_output
    assert "Python output (default):" in error_output
    assert "Hierarchical JSON output:" in error_output
    assert "--mapping and --unmapped apply only to Python output." in error_output
    assert "the following arguments are required: --input, --output" in error_output


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


def test_cli_default_format_preserves_python_output(tmp_path):
    default_output = tmp_path / "default_para.py"
    explicit_output = tmp_path / "explicit_para.py"
    common_args = [
        "--input",
        str(FIXTURE_PATH),
        "--mapping",
        str(MAPPING_PATH),
    ]

    assert main(common_args + ["--output", str(default_output)]) == 0
    assert (
        main(
            common_args
            + ["--format", "python", "--output", str(explicit_output)]
        )
        == 0
    )
    assert default_output.read_bytes() == explicit_output.read_bytes()


def test_cli_generates_json_output(tmp_path):
    output_path = tmp_path / "generated_table.json"

    result = main(
        [
            "--input",
            str(FIXTURE_PATH),
            "--format",
            "json",
            "--output",
            str(output_path),
        ]
    )

    assert result == 0
    generated = output_path.read_text(encoding="utf-8")
    document = json.loads(generated)
    assert document["format"] == JSON_FORMAT
    assert document["roots"][0]["name"] == "packet_param"
    assert document["roots"][0]["children"][0]["name"] == "header0"
    assert generated.endswith("\n")
    assert not generated.endswith("\n\n")


def test_committed_demo_output_matches_current_generator():
    parsed_items = parse_uvm_table_text(FIXTURE_PATH.read_text(encoding="utf-8"))
    name_map, keep_unmapped = load_mapping_file(str(MAPPING_PATH))
    mapped_items = apply_mapping(parsed_items, name_map, keep_unmapped)

    assert GENERATED_DEMO_PATH.read_text(encoding="utf-8") == (
        render_python_para_get(mapped_items)
    )


def test_committed_json_demo_matches_current_generator():
    roots = parse_uvm_table_tree(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert GENERATED_JSON_DEMO_PATH.read_text(encoding="utf-8") == (
        render_uvm_table_json(roots)
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


def test_json_cli_rejects_empty_input_without_output(tmp_path, capsys):
    input_path = tmp_path / "empty.txt"
    output_path = tmp_path / "generated_table.json"
    input_path.write_text("UVM_INFO no table here\n", encoding="utf-8")

    result = main(
        [
            "--input",
            str(input_path),
            "--format",
            "json",
            "--output",
            str(output_path),
        ]
    )

    assert result == 1
    assert not output_path.exists()
    assert "no supported table nodes" in capsys.readouterr().err


def test_json_cli_rejects_python_mapping_options(tmp_path, capsys):
    output_path = tmp_path / "generated_table.json"

    result = main(
        [
            "--input",
            str(FIXTURE_PATH),
            "--format",
            "json",
            "--mapping",
            str(MAPPING_PATH),
            "--output",
            str(output_path),
        ]
    )

    assert result == 1
    assert not output_path.exists()
    assert "only valid with --format python" in capsys.readouterr().err


def test_cli_removes_temporary_output_when_atomic_replace_fails(
    tmp_path, capsys, monkeypatch
):
    output_path = tmp_path / "generated_table.json"

    def fail_replace(_source, _destination):
        raise OSError("replace failed")

    monkeypatch.setattr(parser_module.os, "replace", fail_replace)
    result = main(
        [
            "--input",
            str(FIXTURE_PATH),
            "--format",
            "json",
            "--output",
            str(output_path),
        ]
    )

    assert result == 1
    assert not output_path.exists()
    assert list(tmp_path.glob(".uvm_table_*.tmp")) == []
    assert "replace failed" in capsys.readouterr().err
