import json
from copy import deepcopy
from pathlib import Path

from rm_ref.config import UserConfig
from rm_ref.core import Algorithm
from rm_ref.runtime import (
    BINDING_ERROR,
    CONFIG_ERROR,
    EXECUTION_ERROR,
    PARSE_ERROR,
    PASS,
    RUNTIME_COMPLETED,
    VALIDATION_ERROR,
    run_case,
    run_uvm_table_json_case,
    run_uvm_table_text_case,
)
from rm_ref.schema import SchemaDefinition
from utils.parse_uvm_table_print import parse_uvm_table_tree
from utils.uvm_table_config_adapter import bind_config_from_uvm_table_json


CASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
INPUT_TEXT = CASE_DIR / "input_uvm_table_printer.txt"
SCHEMA_JSON = REPO_ROOT / "schema_defs" / "uvm_table" / "demo2_schema.json"


PACKET_TYPE = "cell.header0.packet_type_w0_b31_28"
FPGA_LINK_ID = "cell.header0.fpga_link_id_w0_b27_24"
FRAME_NUM = "cell.header0.frame_num_w0_b23_8"
SLOT_NUM = "cell.header0.slot_num_w0_b7_0"
BSRS = "cell.header0.bsrs_w4_b1_0"
RESERVED = "cell.header0.rsv_word1_b11_w1_b11_11"


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class ParameterCaptureAlgorithm(Algorithm):
    def __init__(self):
        self.calls = []

    def execute_cell(self, cell_ctx):
        parameters = cell_ctx.get_config_snapshot()
        self.calls.append(
            {
                "packet_index": cell_ctx.packet_ctx.packet_cfg.packet_index,
                "cell_index": cell_ctx.cell_cfg.cell_index,
                "parameters": parameters,
                "samples": deepcopy(cell_ctx.get_input("samples", [])),
            }
        )
        cell_ctx.push_output("parameters", parameters)


class FailingAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        raise RuntimeError("algorithm failed")


def _schema():
    return SchemaDefinition.from_dict(_read_json(SCHEMA_JSON))


def _input_text():
    return INPUT_TEXT.read_text(encoding="utf-8")


def _input_json():
    return {
        "format": "uvm_table_printer/v1",
        "roots": parse_uvm_table_tree(_input_text()),
    }


def test_uvm_table_printer_text_becomes_algorithm_readable_parameters():
    schema = _schema()
    roots = parse_uvm_table_tree(_input_text())
    binding = bind_config_from_uvm_table_json(
        {"format": "uvm_table_printer/v1", "roots": roots},
        schema,
    )
    algorithm = ParameterCaptureAlgorithm()

    result = run_case(
        UserConfig.from_dict(binding.config_dict),
        schema,
        algorithm,
        payload_by_packet=None,
    )

    assert not binding.has_errors
    assert binding.report["bound_field_count"] == 16
    assert binding.report["skipped_reserved_count"] == 3
    assert binding.report["skipped_payload_count"] == 1
    assert result.status == PASS
    assert algorithm.calls[0]["packet_index"] == 0
    assert algorithm.calls[0]["cell_index"] == 0
    assert algorithm.calls[0]["samples"] == []

    parameters = algorithm.calls[0]["parameters"]
    assert parameters[PACKET_TYPE] == 10
    assert parameters[FPGA_LINK_ID] == 3
    assert parameters[FRAME_NUM] == 0x1234
    assert parameters[SLOT_NUM] == 0x56
    assert parameters[BSRS] == 2
    assert RESERVED not in parameters
    assert "Payload" not in parameters
    assert "payload" not in parameters

    output_parameters = result.run_result.packet_outputs[0].cell_outputs[0].output[
        "parameters"
    ]
    assert output_parameters[PACKET_TYPE] == 10
    assert output_parameters[BSRS] == 2


def test_run_uvm_table_text_case_reaches_algorithm():
    algorithm = ParameterCaptureAlgorithm()

    result = run_uvm_table_text_case(_input_text(), _schema(), algorithm)

    assert result.status == RUNTIME_COMPLETED
    assert result.parse_report == {
        "root_count": 1,
        "root_names": ["demo2"],
    }
    assert result.orchestration_result.status == PASS
    assert algorithm.calls[0]["parameters"][PACKET_TYPE] == 10
    assert algorithm.calls[0]["parameters"][FRAME_NUM] == 0x1234


def test_run_uvm_table_json_case_reaches_algorithm():
    algorithm = ParameterCaptureAlgorithm()

    result = run_uvm_table_json_case(_input_json(), _schema(), algorithm)

    assert result.status == RUNTIME_COMPLETED
    assert result.orchestration_result.status == PASS
    assert algorithm.calls[0]["parameters"][SLOT_NUM] == 0x56
    assert result.user_config_dict["packets"][0]["cells"][0]["values"][BSRS] == 2


def test_parse_error_blocks_runtime():
    algorithm = ParameterCaptureAlgorithm()

    result = run_uvm_table_text_case("not a uvm table", _schema(), algorithm)

    assert result.status == PARSE_ERROR
    assert result.orchestration_result is None
    assert algorithm.calls == []


def test_binding_error_blocks_runtime():
    document = {
        "format": "uvm_table_printer/v1",
        "roots": [
            {
                "name": "demo2",
                "type": "interface_table",
                "size": None,
                "children": [
                    {
                        "name": "word0",
                        "type": "integral[31:0]",
                        "size": 32,
                        "value": 0,
                    },
                    {
                        "name": "unknown_field",
                        "type": "integral[3:0]",
                        "size": 4,
                        "value": 1,
                    },
                ],
            }
        ],
    }
    algorithm = ParameterCaptureAlgorithm()

    result = run_uvm_table_json_case(document, _schema(), algorithm)

    assert result.status == BINDING_ERROR
    assert result.orchestration_result is None
    assert algorithm.calls == []
    assert result.binding_report["unknown_field_count"] == 1


def test_config_error_blocks_runtime(monkeypatch):
    document = _input_json()
    algorithm = ParameterCaptureAlgorithm()

    import rm_ref.runtime.uvm_table_case as uvm_table_case

    def fail_from_dict(config_dict):
        raise ValueError("bad user config")

    monkeypatch.setattr(uvm_table_case.UserConfig, "from_dict", fail_from_dict)

    result = run_uvm_table_json_case(document, _schema(), algorithm)

    assert result.status == CONFIG_ERROR
    assert result.orchestration_result is None
    assert algorithm.calls == []


def test_validation_error_is_preserved_in_orchestration_result():
    schema_dict = _read_json(SCHEMA_JSON)
    for field in schema_dict["fields"]:
        if field["original_name"] == "packet_type":
            field["max"] = 9
    schema = SchemaDefinition.from_dict(schema_dict)
    algorithm = ParameterCaptureAlgorithm()

    result = run_uvm_table_text_case(_input_text(), schema, algorithm)

    assert result.status == RUNTIME_COMPLETED
    assert result.orchestration_result.status == VALIDATION_ERROR
    assert algorithm.calls == []


def test_algorithm_exception_is_preserved_in_orchestration_result():
    result = run_uvm_table_text_case(_input_text(), _schema(), FailingAlgorithm())

    assert result.status == RUNTIME_COMPLETED
    assert result.orchestration_result.status == EXECUTION_ERROR
    assert str(result.orchestration_result.run_result.exception) == "algorithm failed"


def test_reserved_and_payload_not_visible_to_algorithm():
    algorithm = ParameterCaptureAlgorithm()

    result = run_uvm_table_text_case(_input_text(), _schema(), algorithm)

    assert result.status == RUNTIME_COMPLETED
    assert result.binding_report["skipped_reserved_count"] == 3
    assert result.binding_report["skipped_payload_count"] == 1
    parameters = algorithm.calls[0]["parameters"]
    assert RESERVED not in parameters
    assert "Payload" not in parameters
    assert "payload" not in parameters


def test_uvm_table_case_result_to_dict_embeds_orchestration_result():
    result = run_uvm_table_text_case(
        _input_text(),
        _schema(),
        ParameterCaptureAlgorithm(),
    )

    serialized = result.to_dict()

    assert serialized["status"] == RUNTIME_COMPLETED
    assert serialized["parse_report"]["root_names"] == ["demo2"]
    assert serialized["orchestration_result"]["status"] == PASS
    assert serialized["user_config_dict"]["schema_id"] == "demo2/schema/v1"
