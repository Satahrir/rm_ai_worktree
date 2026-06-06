from rm_ref.core.algorithm import Algorithm
from rm_ref.core.config import CellConfig, PacketConfig, TestcaseConfig
from rm_ref.core.runner import run_config
from rm_ref.core.status import ERROR, OK, WARNING


class EchoAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        samples = cell_ctx.get_input("samples", [])
        cell_ctx.push_output("sample_count", len(samples))


class WarningAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        cell_ctx.warn("SHORT_INPUT", "input is short", minimum=2)


class ErrorAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        cell_ctx.error("BAD_INPUT", "input is invalid", value=-1)


class FailingAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        raise RuntimeError("model failed")


def _packet(samples, cell_index=0):
    return PacketConfig(
        input_pkt_by_cc={cell_index: samples},
        cells=[CellConfig(cell_index=cell_index)],
    )


def test_runner_executes_single_packet_single_cell():
    cfg = TestcaseConfig(case_name="echo", packets=[_packet([1, 2, 3])])

    result = run_config(cfg, EchoAlgorithm())

    assert result.status == OK
    assert result.exit_code == 0
    assert result.case_name == "echo"
    assert result.algorithm_name == "EchoAlgorithm"
    assert result.summary == {
        "packet_count": 1,
        "cell_count": 1,
        "warning_count": 0,
        "error_count": 0,
    }


def test_runner_executes_multiple_packets():
    cfg = TestcaseConfig(
        packets=[_packet([1]), _packet([2, 3], cell_index=4)]
    )

    result = run_config(cfg, EchoAlgorithm())

    assert [item.packet_index for item in result.packet_outputs] == [0, 1]
    assert [
        item.cell_outputs[0].output["sample_count"]
        for item in result.packet_outputs
    ] == [1, 2]


def test_algorithm_output_is_in_cell_result():
    result = run_config(
        TestcaseConfig(packets=[_packet([7, 8])]),
        EchoAlgorithm(),
    )

    cell_output = result.packet_outputs[0].cell_outputs[0]
    assert cell_output.packet_index == 0
    assert cell_output.cell_index == 0
    assert cell_output.output == {"sample_count": 2}


def test_cell_warning_propagates_to_run():
    result = run_config(
        TestcaseConfig(packets=[_packet([])]),
        WarningAlgorithm(),
    )

    packet_output = result.packet_outputs[0]
    cell_output = packet_output.cell_outputs[0]
    assert result.status == WARNING
    assert packet_output.status == WARNING
    assert cell_output.status == WARNING
    assert len(result.warnings) == 1
    assert result.warnings[0].code == "SHORT_INPUT"
    assert result.warnings[0].packet_index == 0
    assert result.warnings[0].cell_index == 0
    assert result.warnings[0].fields == {"minimum": 2}


def test_cell_error_sets_run_error():
    result = run_config(
        TestcaseConfig(packets=[_packet([])]),
        ErrorAlgorithm(),
    )

    assert result.status == ERROR
    assert result.exit_code == 1
    assert result.packet_outputs[0].status == ERROR
    assert result.packet_outputs[0].cell_outputs[0].status == ERROR
    assert result.errors[0].code == "BAD_INPUT"


def test_algorithm_exception_returns_error_result():
    cfg = TestcaseConfig(
        packets=[_packet([1]), _packet([2])]
    )

    result = run_config(cfg, FailingAlgorithm())

    assert result.status == ERROR
    assert result.exit_code == 1
    assert isinstance(result.exception, RuntimeError)
    assert str(result.exception) == "model failed"
    assert result.summary["packet_count"] == 1
    assert result.summary["cell_count"] == 1
    assert result.errors[0].code == "ALGORITHM_EXCEPTION"
    assert result.errors[0].fields["exception_type"] == "RuntimeError"


def test_static_config_is_not_mutated_by_runtime_output():
    packet = _packet([1, 2])
    cfg = TestcaseConfig(packets=[packet])

    result = run_config(cfg, EchoAlgorithm())
    result.packet_outputs[0].cell_outputs[0].output["sample_count"] = 99

    assert packet.input_pkt_by_cc == {0: [1, 2]}
    assert packet.cells[0].parameters == {}
