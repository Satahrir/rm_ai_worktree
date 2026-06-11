import pytest

from rm_ref.core.algorithm import Algorithm
from rm_ref.core.config import CellConfig, PacketConfig, TestcaseConfig
from rm_ref.core.diagnostic import Diagnostic, ERROR as DIAGNOSTIC_ERROR
from rm_ref.core.lifecycle import prepare_run
from rm_ref.core.pipeline import execute_pipeline
from rm_ref.core.result import CellOutput, PacketOutput, RunResult
from rm_ref.core.runner import run_config
from rm_ref.core.status import ERROR, OK


class RecordingAlgorithm(Algorithm):
    def __init__(self, fail_at=None):
        self.fail_at = fail_at
        self.executed = []

    def execute_cell(self, cell_ctx):
        location = (
            cell_ctx.packet_ctx.packet_cfg.packet_index,
            cell_ctx.cell_cfg.cell_index,
        )
        self.executed.append(location)
        if location == self.fail_at:
            raise RuntimeError("failed at {0}".format(location))
        cell_ctx.push_output("location", location)


def _config(packet_cell_indexes):
    packets = []
    for packet_index, cell_indexes in enumerate(packet_cell_indexes):
        packets.append(
            PacketConfig(
                packet_index=packet_index,
                cells=[
                    CellConfig(cell_index=cell_index)
                    for cell_index in cell_indexes
                ],
            )
        )
    return TestcaseConfig(case_name="hardening", packets=packets)


def _assert_plain(value):
    if isinstance(value, dict):
        for key, item in value.items():
            assert isinstance(key, (type(None), bool, int, float, str))
            _assert_plain(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_plain(item)
        return
    assert isinstance(value, (type(None), bool, int, float, str))


def test_successful_pipeline_finalizes_all_started_contexts():
    rm_ctx = prepare_run(_config([[0, 1], [4]]))
    algorithm = RecordingAlgorithm()

    execute_pipeline(rm_ctx, algorithm)

    assert algorithm.executed == [(0, 0), (0, 1), (1, 4)]
    assert rm_ctx.runtime["state"] == {
        "packet_count": 2,
        "completed": True,
        "executed_packet_count": 2,
    }
    for packet_ctx in rm_ctx.packet_contexts:
        assert packet_ctx.runtime["state"]["completed"] is True
        assert packet_ctx.runtime["state"]["executed_cell_count"] == len(
            packet_ctx.cell_contexts
        )
        assert all(
            cell_ctx.runtime["state"]["completed"] is True
            for cell_ctx in packet_ctx.cell_contexts
        )


def test_first_cell_exception_finalizes_active_contexts_and_stops_traversal():
    rm_ctx = prepare_run(_config([[0, 1], [0]]))
    algorithm = RecordingAlgorithm(fail_at=(0, 0))

    with pytest.raises(RuntimeError, match="failed at"):
        execute_pipeline(rm_ctx, algorithm)

    packet_ctx = rm_ctx.packet_contexts[0]
    cell_ctx = packet_ctx.cell_contexts[0]
    assert algorithm.executed == [(0, 0)]
    assert len(rm_ctx.packet_contexts) == 1
    assert len(packet_ctx.cell_contexts) == 1
    assert cell_ctx.runtime["state"]["completed"] is True
    assert packet_ctx.runtime["state"] == {
        "completed": True,
        "executed_cell_count": 1,
    }
    assert rm_ctx.runtime["state"] == {
        "packet_count": 2,
        "completed": True,
        "executed_packet_count": 1,
    }
    assert [item.code for item in cell_ctx.errors] == [
        "ALGORITHM_EXCEPTION"
    ]
    assert [item.code for item in packet_ctx.errors] == [
        "ALGORITHM_EXCEPTION"
    ]
    assert [item.code for item in rm_ctx.errors] == [
        "ALGORITHM_EXCEPTION"
    ]


def test_later_cell_exception_preserves_completed_counts_and_fail_fast():
    rm_ctx = prepare_run(_config([[0, 1, 2], [0]]))
    algorithm = RecordingAlgorithm(fail_at=(0, 1))

    with pytest.raises(RuntimeError, match="failed at"):
        execute_pipeline(rm_ctx, algorithm)

    packet_ctx = rm_ctx.packet_contexts[0]
    assert algorithm.executed == [(0, 0), (0, 1)]
    assert len(rm_ctx.packet_contexts) == 1
    assert len(packet_ctx.cell_contexts) == 2
    assert packet_ctx.runtime["state"]["completed"] is True
    assert packet_ctx.runtime["state"]["executed_cell_count"] == 2
    assert rm_ctx.runtime["state"]["completed"] is True
    assert rm_ctx.runtime["state"]["executed_packet_count"] == 1
    assert all(
        cell_ctx.runtime["state"]["completed"] is True
        for cell_ctx in packet_ctx.cell_contexts
    )


def test_diagnostic_to_dict_is_deterministic_and_deep_copied():
    diagnostic = Diagnostic(
        DIAGNOSTIC_ERROR,
        "BAD_VALUE",
        "value is invalid",
        packet_index=3,
        cell_index=5,
        fields={"nested": {"values": [1, 2]}, "pair": (4, 6)},
    )

    serialized = diagnostic.to_dict()

    assert list(serialized.keys()) == [
        "severity",
        "code",
        "message",
        "packet_index",
        "cell_index",
        "fields",
    ]
    assert serialized == diagnostic.to_dict()
    assert serialized["fields"]["pair"] == [4, 6]
    serialized["fields"]["nested"]["values"].append(3)
    assert diagnostic.fields["nested"]["values"] == [1, 2]
    _assert_plain(serialized)


def test_cell_output_to_dict_preserves_output_and_diagnostics():
    warning = Diagnostic(
        "warning",
        "SHORT_INPUT",
        "input is short",
        packet_index=2,
        cell_index=7,
    )
    cell_output = CellOutput(
        packet_index=2,
        cell_index=7,
        status="WARNING",
        warnings=[warning],
        output={"samples": [1, 2], "shape": (1, 2)},
    )

    serialized = cell_output.to_dict()

    assert serialized["packet_index"] == 2
    assert serialized["cell_index"] == 7
    assert serialized["status"] == "WARNING"
    assert serialized["warnings"][0]["code"] == "SHORT_INPUT"
    assert serialized["errors"] == []
    assert serialized["output"] == {
        "samples": [1, 2],
        "shape": [1, 2],
    }
    serialized["output"]["samples"].append(3)
    assert cell_output.output["samples"] == [1, 2]
    _assert_plain(serialized)


def test_packet_output_to_dict_preserves_summary_and_cell_outputs():
    cell_output = CellOutput(1, 4, OK, output={"value": 9})
    packet_output = PacketOutput(
        packet_index=1,
        status=OK,
        runtime_summary={
            "active_cell_count": 1,
            "executed_cell_count": 1,
        },
        cell_outputs=[cell_output],
    )

    serialized = packet_output.to_dict()

    assert serialized == {
        "packet_index": 1,
        "status": OK,
        "warnings": [],
        "errors": [],
        "runtime_summary": {
            "active_cell_count": 1,
            "executed_cell_count": 1,
        },
        "cell_outputs": [
            {
                "packet_index": 1,
                "cell_index": 4,
                "status": OK,
                "warnings": [],
                "errors": [],
                "output": {"value": 9},
            }
        ],
    }
    serialized["runtime_summary"]["executed_cell_count"] = 99
    serialized["cell_outputs"][0]["output"]["value"] = 10
    assert packet_output.runtime_summary["executed_cell_count"] == 1
    assert cell_output.output["value"] == 9
    _assert_plain(serialized)


def test_successful_run_result_to_dict_is_complete_and_stable():
    result = run_config(_config([[0], [3]]), RecordingAlgorithm())

    serialized = result.to_dict()

    assert serialized == result.to_dict()
    assert serialized["status"] == OK
    assert serialized["exit_code"] == 0
    assert serialized["case_name"] == "hardening"
    assert serialized["algorithm_name"] == "RecordingAlgorithm"
    assert serialized["summary"] == {
        "cell_count": 2,
        "error_count": 0,
        "packet_count": 2,
        "warning_count": 0,
    }
    assert [item["packet_index"] for item in serialized["packet_outputs"]] == [
        0,
        1,
    ]
    assert serialized["warnings"] == []
    assert serialized["errors"] == []
    assert serialized["exception"] is None
    _assert_plain(serialized)


def test_exception_run_result_to_dict_uses_stable_exception_metadata():
    result = run_config(
        _config([[0, 1], [0]]),
        RecordingAlgorithm(fail_at=(0, 0)),
    )

    serialized = result.to_dict()

    assert result.status == ERROR
    assert isinstance(result.exception, RuntimeError)
    assert serialized["exception"] == {
        "type": "RuntimeError",
        "message": "failed at (0, 0)",
    }
    assert serialized["summary"]["packet_count"] == 1
    assert serialized["summary"]["cell_count"] == 1
    assert serialized["errors"][0]["code"] == "ALGORITHM_EXCEPTION"
    assert (
        serialized["packet_outputs"][0]["errors"][0]["code"]
        == "ALGORITHM_EXCEPTION"
    )
    assert (
        serialized["packet_outputs"][0]["cell_outputs"][0]["errors"][0][
            "code"
        ]
        == "ALGORITHM_EXCEPTION"
    )
    _assert_plain(serialized)


def test_run_result_to_dict_does_not_share_mutable_values():
    diagnostic = Diagnostic(
        DIAGNOSTIC_ERROR,
        "FAIL",
        "failed",
        fields={"details": ["original"]},
    )
    cell_output = CellOutput(
        0,
        0,
        ERROR,
        errors=[diagnostic],
        output={"values": [1]},
    )
    packet_output = PacketOutput(
        0,
        ERROR,
        errors=[diagnostic],
        runtime_summary={"counts": [1]},
        cell_outputs=[cell_output],
    )
    result = RunResult(
        ERROR,
        1,
        "case",
        "Algorithm",
        summary={"counts": [1]},
        packet_outputs=[packet_output],
        errors=[diagnostic],
        exception=RuntimeError("failed"),
    )

    serialized = result.to_dict()
    serialized["summary"]["counts"].append(2)
    serialized["packet_outputs"][0]["runtime_summary"]["counts"].append(2)
    serialized["packet_outputs"][0]["cell_outputs"][0]["output"][
        "values"
    ].append(2)
    serialized["errors"][0]["fields"]["details"].append("changed")

    assert result.summary["counts"] == [1]
    assert packet_output.runtime_summary["counts"] == [1]
    assert cell_output.output["values"] == [1]
    assert diagnostic.fields["details"] == ["original"]
