import copy

from rm_ref.core.algorithm import Algorithm
from rm_ref.core.config import CellConfig, PacketConfig, TestcaseConfig
from rm_ref.core.runner import run_config
from rm_ref.core.status import ERROR, OK, WARNING


class EchoAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        samples = cell_ctx.get_input("samples", [])
        cell_ctx.push_output("sample_count", len(samples))


class WarningAlgorithm(EchoAlgorithm):
    def execute_cell(self, cell_ctx):
        EchoAlgorithm.execute_cell(self, cell_ctx)
        cell_ctx.warn("SHORT_INPUT", "input is short", minimum=2)


class ErrorAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        cell_ctx.error(
            "BAD_INPUT",
            "input is invalid",
            field_name="samples",
            value=-1,
        )


class FailingAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        raise RuntimeError("model failed")


class MutatingInputAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        samples = cell_ctx.get_input("samples", [])
        initial_samples = copy.deepcopy(samples)
        if cell_ctx.cell_cfg.cell_index == 0:
            samples.append({"mutated_by": 0})

        packet_by_cc = cell_ctx.packet_ctx.get_input("packet_by_cc")
        cell_ctx.push_output("initial_samples", initial_samples)
        cell_ctx.push_output(
            "packet_samples_after",
            copy.deepcopy(packet_by_cc.get(cell_ctx.cell_cfg.cell_index)),
        )


def _packet(samples, cell_index=0):
    return PacketConfig(
        parameters={"packet_mode": "test"},
        input_pkt_by_cc={cell_index: samples},
        cells=[
            CellConfig(
                cell_index=cell_index,
                parameters={"enabled": True},
            )
        ],
    )


def test_runner_executes_single_packet_single_cell_and_propagates_output():
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
    assert len(result.packet_outputs) == 1

    packet_output = result.packet_outputs[0]
    assert packet_output.packet_index == 0
    assert len(packet_output.cell_outputs) == 1

    cell_output = packet_output.cell_outputs[0]
    assert cell_output.packet_index == 0
    assert cell_output.cell_index == 0
    assert cell_output.status == OK
    assert cell_output.output == {"sample_count": 3}


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


def test_missing_cell_input_is_exposed_as_an_empty_sample_list():
    cfg = TestcaseConfig(
        packets=[PacketConfig(cells=[CellConfig(cell_index=7)])]
    )

    result = run_config(cfg, EchoAlgorithm())

    assert result.status == OK
    assert result.packet_outputs[0].cell_outputs[0].output["sample_count"] == 0


def test_cell_warning_propagates_to_packet_and_run():
    result = run_config(
        TestcaseConfig(packets=[_packet([1])]),
        WarningAlgorithm(),
    )

    packet_output = result.packet_outputs[0]
    cell_output = packet_output.cell_outputs[0]

    assert result.status == WARNING
    assert packet_output.status == WARNING
    assert cell_output.status == WARNING
    assert [item.code for item in cell_output.warnings] == ["SHORT_INPUT"]
    assert [item.code for item in packet_output.warnings] == ["SHORT_INPUT"]
    assert [item.code for item in result.warnings] == ["SHORT_INPUT"]
    assert result.warnings[0].packet_index == 0
    assert result.warnings[0].cell_index == 0
    assert result.warnings[0].fields == {"minimum": 2}


def test_cell_error_propagates_and_sets_error_result():
    result = run_config(
        TestcaseConfig(packets=[_packet([])]),
        ErrorAlgorithm(),
    )

    packet_output = result.packet_outputs[0]
    cell_output = packet_output.cell_outputs[0]

    assert result.status == ERROR
    assert result.exit_code == 1
    assert packet_output.status == ERROR
    assert cell_output.status == ERROR
    assert [item.code for item in cell_output.errors] == ["BAD_INPUT"]
    assert [item.code for item in packet_output.errors] == ["BAD_INPUT"]
    assert [item.code for item in result.errors] == ["BAD_INPUT"]
    assert result.errors[0].fields == {
        "field_name": "samples",
        "value": -1,
    }


def test_algorithm_exception_returns_structured_error_result():
    cfg = TestcaseConfig(packets=[_packet([1]), _packet([2])])

    result = run_config(cfg, FailingAlgorithm())

    assert result.status == ERROR
    assert result.exit_code == 1
    assert isinstance(result.exception, RuntimeError)
    assert str(result.exception) == "model failed"
    assert result.summary["packet_count"] == 1
    assert result.summary["cell_count"] == 1
    assert result.errors[0].code == "ALGORITHM_EXCEPTION"
    assert result.errors[0].fields["exception_type"] == "RuntimeError"


def test_runtime_output_does_not_mutate_static_config():
    packet = _packet([4, 5])
    cfg = TestcaseConfig(packets=[packet])
    original_global_parameters = copy.deepcopy(cfg.global_cfg.parameters)
    original_packet_parameters = copy.deepcopy(packet.parameters)
    original_cell_parameters = copy.deepcopy(packet.cells[0].parameters)
    original_input = copy.deepcopy(packet.input_pkt_by_cc)

    result = run_config(cfg, EchoAlgorithm())
    result.packet_outputs[0].cell_outputs[0].output["sample_count"] = 99

    assert cfg.global_cfg.parameters == original_global_parameters
    assert packet.parameters == original_packet_parameters
    assert packet.cells[0].parameters == original_cell_parameters
    assert packet.input_pkt_by_cc == original_input
    assert not hasattr(packet.cells[0], "output")


def test_algorithm_input_mutation_does_not_mutate_caller_or_static_payload():
    caller_samples = [{"value": 4}]
    packet = _packet(caller_samples)
    original_caller_samples = copy.deepcopy(caller_samples)
    original_static_input = copy.deepcopy(packet.input_pkt_by_cc)

    run_config(TestcaseConfig(packets=[packet]), MutatingInputAlgorithm())

    assert caller_samples == original_caller_samples
    assert packet.input_pkt_by_cc == original_static_input


def test_shared_source_payload_does_not_contaminate_another_cell():
    shared_samples = [{"value": 1}]
    packet = PacketConfig(
        input_pkt_by_cc={0: shared_samples, 1: shared_samples},
        cells=[CellConfig(cell_index=0), CellConfig(cell_index=1)],
    )

    result = run_config(
        TestcaseConfig(packets=[packet]),
        MutatingInputAlgorithm(),
    )

    cell_outputs = result.packet_outputs[0].cell_outputs
    assert cell_outputs[0].output["packet_samples_after"] == [
        {"value": 1},
        {"mutated_by": 0},
    ]
    assert cell_outputs[1].output["initial_samples"] == [{"value": 1}]
    assert cell_outputs[1].output["packet_samples_after"] == [{"value": 1}]


def test_missing_cell_inputs_are_independent_empty_working_payloads():
    packet = PacketConfig(
        cells=[CellConfig(cell_index=0), CellConfig(cell_index=1)],
    )

    result = run_config(
        TestcaseConfig(packets=[packet]),
        MutatingInputAlgorithm(),
    )

    cell_outputs = result.packet_outputs[0].cell_outputs
    assert cell_outputs[0].output["initial_samples"] == []
    assert cell_outputs[0].output["packet_samples_after"] == [
        {"mutated_by": 0}
    ]
    assert cell_outputs[1].output["initial_samples"] == []
    assert cell_outputs[1].output["packet_samples_after"] == []
