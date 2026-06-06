import copy

import pytest


algorithm_module = pytest.importorskip(
    "rm_ref.core.algorithm",
    reason="Core Agent must implement rm_ref.core.algorithm before runner tests can run",
)
config_module = pytest.importorskip(
    "rm_ref.core.config",
    reason="Core Agent must implement rm_ref.core.config before runner tests can run",
)
runner_module = pytest.importorskip(
    "rm_ref.core.runner",
    reason="Core Agent must implement rm_ref.core.runner before runner tests can run",
)
status_module = pytest.importorskip(
    "rm_ref.core.status",
    reason="Core Agent must implement rm_ref.core.status before runner tests can run",
)

Algorithm = algorithm_module.Algorithm
CellConfig = config_module.CellConfig
PacketConfig = config_module.PacketConfig
TestcaseConfig = config_module.TestcaseConfig
run_config = runner_module.run_config
OK = status_module.OK
WARNING = status_module.WARNING
ERROR = status_module.ERROR


class EchoAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        samples = cell_ctx.get_input("samples", [])
        cell_ctx.push_output("sample_count", len(samples))


class WarningAlgorithm(EchoAlgorithm):
    def execute_cell(self, cell_ctx):
        EchoAlgorithm.execute_cell(self, cell_ctx)
        cell_ctx.warn("SHORT_INPUT", "input contains fewer than two samples")


class ErrorAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        cell_ctx.error("INVALID_INPUT", "input is invalid", field_name="samples")


class RaisingAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        raise RuntimeError("algorithm failed")


def make_single_cell_config(samples=None):
    if samples is None:
        samples = []
    return TestcaseConfig(
        case_name="single-cell",
        packets=[
            PacketConfig(
                parameters={"packet_mode": "test"},
                input_pkt_by_cc={0: samples},
                cells=[CellConfig(parameters={"enabled": True})],
            )
        ],
    )


def test_runner_executes_single_packet_single_cell_and_propagates_output():
    result = run_config(make_single_cell_config([1, 2, 3]), EchoAlgorithm())

    assert result.status == OK
    assert result.exit_code == 0
    assert result.case_name == "single-cell"
    assert result.algorithm_name == "EchoAlgorithm"
    assert len(result.packet_outputs) == 1

    packet_output = result.packet_outputs[0]
    assert packet_output.packet_index == 0
    assert len(packet_output.cell_outputs) == 1

    cell_output = packet_output.cell_outputs[0]
    assert cell_output.packet_index == 0
    assert cell_output.cell_index == 0
    assert cell_output.status == OK
    assert cell_output.output["sample_count"] == 3


def test_missing_cell_input_is_exposed_as_an_empty_sample_list():
    result = run_config(make_single_cell_config(), EchoAlgorithm())

    assert result.status == OK
    assert result.packet_outputs[0].cell_outputs[0].output["sample_count"] == 0


def test_cell_warning_propagates_to_packet_and_run():
    result = run_config(make_single_cell_config([1]), WarningAlgorithm())

    packet_output = result.packet_outputs[0]
    cell_output = packet_output.cell_outputs[0]

    assert result.status == WARNING
    assert packet_output.status == WARNING
    assert cell_output.status == WARNING
    assert [diagnostic.code for diagnostic in cell_output.warnings] == ["SHORT_INPUT"]
    assert [diagnostic.code for diagnostic in packet_output.warnings] == ["SHORT_INPUT"]
    assert [diagnostic.code for diagnostic in result.warnings] == ["SHORT_INPUT"]
    assert result.warnings[0].packet_index == 0
    assert result.warnings[0].cell_index == 0


def test_cell_error_propagates_and_sets_error_result():
    result = run_config(make_single_cell_config([1]), ErrorAlgorithm())

    packet_output = result.packet_outputs[0]
    cell_output = packet_output.cell_outputs[0]

    assert result.status == ERROR
    assert result.exit_code != 0
    assert packet_output.status == ERROR
    assert cell_output.status == ERROR
    assert [diagnostic.code for diagnostic in cell_output.errors] == ["INVALID_INPUT"]
    assert [diagnostic.code for diagnostic in packet_output.errors] == ["INVALID_INPUT"]
    assert [diagnostic.code for diagnostic in result.errors] == ["INVALID_INPUT"]
    assert result.errors[0].fields["field_name"] == "samples"


def test_algorithm_exception_returns_structured_error_result():
    result = run_config(make_single_cell_config([1]), RaisingAlgorithm())

    assert result.status == ERROR
    assert result.exit_code != 0
    assert result.exception is not None
    assert "algorithm failed" in str(result.exception)


def test_runtime_output_does_not_mutate_static_config():
    cfg = make_single_cell_config([4, 5])
    original_global_cfg = copy.deepcopy(cfg.global_cfg)
    original_packet_parameters = copy.deepcopy(cfg.packets[0].parameters)
    original_cell_parameters = copy.deepcopy(cfg.packets[0].cells[0].parameters)
    original_input = copy.deepcopy(cfg.packets[0].input_pkt_by_cc)

    result = run_config(cfg, EchoAlgorithm())

    assert result.status == OK
    assert cfg.global_cfg == original_global_cfg
    assert cfg.packets[0].parameters == original_packet_parameters
    assert cfg.packets[0].cells[0].parameters == original_cell_parameters
    assert cfg.packets[0].input_pkt_by_cc == original_input
    assert not hasattr(cfg.packets[0].cells[0], "output")
