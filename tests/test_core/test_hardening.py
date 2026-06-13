import pytest

import rm_ref.core.lifecycle as lifecycle
import rm_ref.core.runner as runner
from rm_ref.core.algorithm import Algorithm
from rm_ref.core.config import CellConfig, PacketConfig, TestcaseConfig
from rm_ref.core.context import CellContext
from rm_ref.core.diagnostic import Diagnostic, ERROR as DIAGNOSTIC_ERROR
from rm_ref.core.errors import (
    AlgorithmContextUsageError,
    AlgorithmExecutionError,
    ConfigError,
    CoreError,
    DiagnosticRecordingError,
    FrameworkError,
    LifecycleFinalizationError,
)
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


def _patch_finalizers(monkeypatch, failing_scopes):
    failures = dict(
        (
            scope,
            RuntimeError("{0} finalizer failed".format(scope)),
        )
        for scope in failing_scopes
    )
    return _patch_finalizer_failures(monkeypatch, failures)


def _patch_finalizer_failures(monkeypatch, failures):
    events = []
    originals = {
        "cell": lifecycle.finalize_cell,
        "packet": lifecycle.finalize_packet,
        "run": lifecycle.finalize_run,
    }

    def make_finalizer(scope):
        def finalizer(ctx):
            events.append(scope)
            originals[scope](ctx)
            if scope in failures:
                raise failures[scope]
        return finalizer

    monkeypatch.setattr(lifecycle, "finalize_cell", make_finalizer("cell"))
    monkeypatch.setattr(
        lifecycle,
        "finalize_packet",
        make_finalizer("packet"),
    )
    monkeypatch.setattr(lifecycle, "finalize_run", make_finalizer("run"))
    return events


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
    assert rm_ctx._lifecycle_state == "FINALIZED"
    for packet_ctx in rm_ctx.packet_contexts:
        assert packet_ctx._lifecycle_state == "FINALIZED"
        assert packet_ctx.runtime["state"]["completed"] is True
        assert packet_ctx.runtime["state"]["executed_cell_count"] == len(
            packet_ctx.cell_contexts
        )
        assert all(
            cell_ctx.runtime["state"]["completed"] is True
            for cell_ctx in packet_ctx.cell_contexts
        )
        assert all(
            cell_ctx._lifecycle_state == "FINALIZED"
            for cell_ctx in packet_ctx.cell_contexts
        )


def test_first_cell_exception_finalizes_active_contexts_and_stops_traversal():
    rm_ctx = prepare_run(_config([[0, 1], [0]]))
    algorithm = RecordingAlgorithm(fail_at=(0, 0))

    with pytest.raises(AlgorithmExecutionError) as exc_info:
        execute_pipeline(rm_ctx, algorithm)

    assert isinstance(exc_info.value.original_exception, RuntimeError)
    assert "failed at" in str(exc_info.value.original_exception)
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

    with pytest.raises(AlgorithmExecutionError) as exc_info:
        execute_pipeline(rm_ctx, algorithm)

    assert isinstance(exc_info.value.original_exception, RuntimeError)
    assert "failed at" in str(exc_info.value.original_exception)
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


@pytest.mark.parametrize(
    "exception",
    [
        RuntimeError("runtime failed"),
        KeyError("missing"),
        AlgorithmContextUsageError("invalid context use"),
    ],
)
def test_callback_exception_is_classified_as_algorithm_failure(exception):
    class FailingAlgorithm(Algorithm):
        def execute_cell(self, cell_ctx):
            raise exception

    result = run_config(_config([[0]]), FailingAlgorithm())

    assert result.status == ERROR
    assert result.exit_code == 1
    assert result.exception is exception
    assert result.errors[0].code == "ALGORITHM_EXCEPTION"
    assert result.errors[0].fields["exception_type"] == (
        exception.__class__.__name__
    )


def test_framework_error_escaping_callback_propagates():
    error = FrameworkError("framework failed")

    class FailingAlgorithm(Algorithm):
        def execute_cell(self, cell_ctx):
            raise error

    with pytest.raises(FrameworkError) as exc_info:
        run_config(_config([[0]]), FailingAlgorithm())

    assert exc_info.value is error


def test_config_error_is_api_contract_error_not_framework_error():
    assert issubclass(ConfigError, CoreError)
    assert not issubclass(ConfigError, FrameworkError)

    with pytest.raises(ConfigError, match="cfg must be TestcaseConfig"):
        run_config(object(), RecordingAlgorithm())


def test_base_exception_escaping_callback_is_not_caught(monkeypatch):
    events = _patch_finalizers(monkeypatch, set())

    class InterruptingAlgorithm(Algorithm):
        def execute_cell(self, cell_ctx):
            raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        run_config(_config([[0]]), InterruptingAlgorithm())

    assert events == ["cell", "packet", "run"]


def test_prepare_run_keyboard_interrupt_finalizes_active_run(monkeypatch):
    events = []
    finalized_contexts = []
    interrupt = KeyboardInterrupt()
    original_finalize_run = lifecycle.finalize_run

    def record_finalize_run(rm_ctx):
        events.append("run")
        finalized_contexts.append(rm_ctx)
        original_finalize_run(rm_ctx)

    def interrupt_initialization(rm_ctx, cfg):
        raise interrupt

    monkeypatch.setattr(lifecycle, "finalize_run", record_finalize_run)
    monkeypatch.setattr(
        lifecycle,
        "_initialize_run_context",
        interrupt_initialization,
    )

    with pytest.raises(KeyboardInterrupt) as exc_info:
        prepare_run(_config([[0]]))

    assert exc_info.value is interrupt
    assert events == ["run"]
    assert finalized_contexts[0]._lifecycle_state == "FINALIZED"
    assert finalized_contexts[0].runtime["state"]["completed"] is True


def test_prepare_run_base_exception_preserves_finalizer_failure(monkeypatch):
    interrupt = KeyboardInterrupt()
    finalizer_error = RuntimeError("run finalizer failed")
    events = _patch_finalizer_failures(
        monkeypatch,
        {"run": finalizer_error},
    )

    def interrupt_initialization(rm_ctx, cfg):
        raise interrupt

    monkeypatch.setattr(
        lifecycle,
        "_initialize_run_context",
        interrupt_initialization,
    )

    with pytest.raises(LifecycleFinalizationError) as exc_info:
        prepare_run(_config([[0]]))

    assert events == ["run"]
    lifecycle_error = exc_info.value
    assert lifecycle_error.primary_error is interrupt
    assert [item.scope for item in lifecycle_error.finalizer_errors] == ["run"]
    assert lifecycle_error.finalizer_errors[0].exception is finalizer_error


def test_callback_keyboard_interrupt_preserves_cell_finalizer_error(
    monkeypatch,
):
    interrupt = KeyboardInterrupt()
    finalizer_error = RuntimeError("cell finalizer failed")
    events = _patch_finalizer_failures(
        monkeypatch,
        {"cell": finalizer_error},
    )

    class InterruptingAlgorithm(Algorithm):
        def execute_cell(self, cell_ctx):
            raise interrupt

    with pytest.raises(LifecycleFinalizationError) as exc_info:
        run_config(_config([[0, 1]]), InterruptingAlgorithm())

    assert events == ["cell", "packet", "run"]
    lifecycle_error = exc_info.value
    assert isinstance(lifecycle_error, LifecycleFinalizationError)
    assert lifecycle_error.primary_error is interrupt
    assert [item.scope for item in lifecycle_error.finalizer_errors] == [
        "cell"
    ]
    assert lifecycle_error.finalizer_errors[0].exception is finalizer_error


def test_cell_finalizer_system_exit_still_runs_packet_and_run_cleanup(
    monkeypatch,
):
    exit_error = SystemExit(7)
    events = _patch_finalizer_failures(
        monkeypatch,
        {"cell": exit_error},
    )
    algorithm = RecordingAlgorithm()

    with pytest.raises(LifecycleFinalizationError) as exc_info:
        run_config(_config([[0, 1], [0]]), algorithm)

    assert algorithm.executed == [(0, 0)]
    assert events == ["cell", "packet", "run"]
    lifecycle_error = exc_info.value
    assert lifecycle_error.primary_error is None
    assert [item.exception for item in lifecycle_error.finalizer_errors] == [
        exit_error
    ]


def test_base_exception_and_multiple_finalizer_failures_are_preserved_once(
    monkeypatch,
):
    interrupt = KeyboardInterrupt()
    cell_error = RuntimeError("cell finalizer failed")
    packet_error = SystemExit(8)
    run_error = RuntimeError("run finalizer failed")
    events = _patch_finalizer_failures(
        monkeypatch,
        {
            "cell": cell_error,
            "packet": packet_error,
            "run": run_error,
        },
    )

    class InterruptingAlgorithm(Algorithm):
        def execute_cell(self, cell_ctx):
            raise interrupt

    with pytest.raises(LifecycleFinalizationError) as exc_info:
        run_config(_config([[0, 1], [0]]), InterruptingAlgorithm())

    assert events == ["cell", "packet", "run"]
    lifecycle_error = exc_info.value
    assert lifecycle_error.primary_error is interrupt
    assert [item.scope for item in lifecycle_error.finalizer_errors] == [
        "cell",
        "packet",
        "run",
    ]
    assert [
        item.exception for item in lifecycle_error.finalizer_errors
    ] == [cell_error, packet_error, run_error]


def test_locked_base_exception_with_finalizer_failure_is_preserved(
    monkeypatch,
):
    class LockedBaseException(BaseException):
        def __setattr__(self, name, value):
            raise AttributeError("attributes are locked")

    primary_error = LockedBaseException("locked")
    finalizer_error = RuntimeError("cell finalizer failed")
    events = _patch_finalizer_failures(
        monkeypatch,
        {"cell": finalizer_error},
    )

    class FailingAlgorithm(Algorithm):
        def execute_cell(self, cell_ctx):
            raise primary_error

    with pytest.raises(LifecycleFinalizationError) as exc_info:
        run_config(_config([[0]]), FailingAlgorithm())

    assert events == ["cell", "packet", "run"]
    assert exc_info.value.primary_error is primary_error
    assert exc_info.value.finalizer_errors[0].exception is finalizer_error


def test_reused_base_exception_has_no_lifecycle_state_leak(monkeypatch):
    primary_error = KeyboardInterrupt()
    finalizer_error = RuntimeError("cell finalizer failed")
    events = _patch_finalizer_failures(
        monkeypatch,
        {"cell": finalizer_error},
    )

    class FailingAlgorithm(Algorithm):
        def execute_cell(self, cell_ctx):
            raise primary_error

    with pytest.raises(LifecycleFinalizationError) as first_exc:
        run_config(_config([[0]]), FailingAlgorithm())

    assert first_exc.value.primary_error is primary_error
    assert not hasattr(primary_error, "lifecycle_finalization_error")

    monkeypatch.undo()

    with pytest.raises(KeyboardInterrupt) as second_exc:
        run_config(_config([[0]]), FailingAlgorithm())

    assert second_exc.value is primary_error
    assert not hasattr(primary_error, "lifecycle_finalization_error")


def test_prepare_packet_failure_propagates_after_packet_and_run_cleanup(
    monkeypatch,
):
    events = _patch_finalizers(monkeypatch, set())
    error = RuntimeError("packet prepare failed")

    def fail_initialize(packet_ctx, packet_cfg):
        raise error

    monkeypatch.setattr(
        lifecycle,
        "_initialize_packet_context",
        fail_initialize,
    )

    with pytest.raises(RuntimeError) as exc_info:
        run_config(_config([[0]]), RecordingAlgorithm())

    assert exc_info.value is error
    assert events == ["packet", "run"]


def test_prepare_cell_failure_propagates_after_all_active_cleanup(monkeypatch):
    events = _patch_finalizers(monkeypatch, set())
    error = RuntimeError("cell prepare failed")

    def fail_initialize(cell_ctx, cell_cfg):
        raise error

    monkeypatch.setattr(
        lifecycle,
        "_initialize_cell_context",
        fail_initialize,
    )

    with pytest.raises(RuntimeError) as exc_info:
        run_config(_config([[0]]), RecordingAlgorithm())

    assert exc_info.value is error
    assert events == ["cell", "packet", "run"]


def test_cell_finalizer_failure_stops_traversal_and_runs_outer_cleanup(
    monkeypatch,
):
    events = _patch_finalizers(monkeypatch, {"cell"})
    algorithm = RecordingAlgorithm()

    with pytest.raises(LifecycleFinalizationError) as exc_info:
        run_config(_config([[0, 1], [0]]), algorithm)

    error = exc_info.value
    assert algorithm.executed == [(0, 0)]
    assert events == ["cell", "packet", "run"]
    assert error.primary_error is None
    assert [item.scope for item in error.finalizer_errors] == ["cell"]
    assert str(error.finalizer_errors[0].exception) == (
        "cell finalizer failed"
    )


def test_packet_finalizer_failure_stops_later_packets_and_cleans_run(
    monkeypatch,
):
    events = _patch_finalizers(monkeypatch, {"packet"})
    algorithm = RecordingAlgorithm()

    with pytest.raises(LifecycleFinalizationError) as exc_info:
        run_config(_config([[0], [0]]), algorithm)

    assert algorithm.executed == [(0, 0)]
    assert events == ["cell", "packet", "run"]
    assert [item.scope for item in exc_info.value.finalizer_errors] == [
        "packet"
    ]


def test_run_finalizer_failure_prevents_result_creation(monkeypatch):
    events = _patch_finalizers(monkeypatch, {"run"})

    with pytest.raises(LifecycleFinalizationError) as exc_info:
        run_config(_config([[0]]), RecordingAlgorithm())

    assert events == ["cell", "packet", "run"]
    assert [item.scope for item in exc_info.value.finalizer_errors] == ["run"]


def test_multiple_finalizer_failures_are_preserved_without_retry(monkeypatch):
    events = _patch_finalizers(monkeypatch, {"cell", "packet", "run"})

    with pytest.raises(LifecycleFinalizationError) as exc_info:
        run_config(_config([[0, 1], [0]]), RecordingAlgorithm())

    assert events == ["cell", "packet", "run"]
    assert [item.scope for item in exc_info.value.finalizer_errors] == [
        "cell",
        "packet",
        "run",
    ]
    assert [str(item.exception) for item in exc_info.value.finalizer_errors] == [
        "cell finalizer failed",
        "packet finalizer failed",
        "run finalizer failed",
    ]


def test_algorithm_exception_plus_finalizer_failure_preserves_both(
    monkeypatch,
):
    events = _patch_finalizers(monkeypatch, {"cell"})
    algorithm = RecordingAlgorithm(fail_at=(0, 0))

    with pytest.raises(LifecycleFinalizationError) as exc_info:
        run_config(_config([[0, 1]]), algorithm)

    error = exc_info.value
    assert events == ["cell", "packet", "run"]
    assert isinstance(error.primary_error, AlgorithmExecutionError)
    assert isinstance(error.primary_error.original_exception, RuntimeError)
    assert [item.scope for item in error.finalizer_errors] == ["cell"]


def test_reported_algorithm_error_plus_finalizer_failure_does_not_return(
    monkeypatch,
):
    _patch_finalizers(monkeypatch, {"cell"})

    class ReportingAlgorithm(Algorithm):
        def execute_cell(self, cell_ctx):
            cell_ctx.error("REPORTED", "reported failure")

    with pytest.raises(LifecycleFinalizationError) as exc_info:
        run_config(_config([[0]]), ReportingAlgorithm())

    assert exc_info.value.primary_error is None


def test_diagnostic_recording_failure_preserves_both_exceptions(monkeypatch):
    algorithm_error = RuntimeError("algorithm failed")
    recording_error = RuntimeError("recording failed")

    class FailingAlgorithm(Algorithm):
        def execute_cell(self, cell_ctx):
            raise algorithm_error

    def fail_recording(self, code, message, **fields):
        raise recording_error

    monkeypatch.setattr(CellContext, "error", fail_recording)

    with pytest.raises(DiagnosticRecordingError) as exc_info:
        run_config(_config([[0]]), FailingAlgorithm())

    assert exc_info.value.primary_error is algorithm_error
    assert exc_info.value.recording_error is recording_error


def test_diagnostic_and_finalizer_failures_preserve_all_errors(monkeypatch):
    _patch_finalizers(monkeypatch, {"cell"})
    algorithm_error = RuntimeError("algorithm failed")
    recording_error = RuntimeError("recording failed")

    class FailingAlgorithm(Algorithm):
        def execute_cell(self, cell_ctx):
            raise algorithm_error

    def fail_recording(self, code, message, **fields):
        raise recording_error

    monkeypatch.setattr(CellContext, "error", fail_recording)

    with pytest.raises(LifecycleFinalizationError) as exc_info:
        run_config(_config([[0]]), FailingAlgorithm())

    primary_error = exc_info.value.primary_error
    assert isinstance(primary_error, DiagnosticRecordingError)
    assert primary_error.primary_error is algorithm_error
    assert primary_error.recording_error is recording_error
    assert [item.scope for item in exc_info.value.finalizer_errors] == ["cell"]


def test_prepare_failure_plus_finalizer_failures_preserves_all_errors(
    monkeypatch,
):
    events = _patch_finalizers(monkeypatch, {"packet", "run"})
    prepare_error = RuntimeError("cell prepare failed")

    def fail_initialize(cell_ctx, cell_cfg):
        raise prepare_error

    monkeypatch.setattr(
        lifecycle,
        "_initialize_cell_context",
        fail_initialize,
    )

    with pytest.raises(LifecycleFinalizationError) as exc_info:
        run_config(_config([[0]]), RecordingAlgorithm())

    assert events == ["cell", "packet", "run"]
    assert exc_info.value.primary_error is prepare_error
    assert [item.scope for item in exc_info.value.finalizer_errors] == [
        "packet",
        "run",
    ]


def test_result_construction_failure_propagates_after_cleanup(monkeypatch):
    events = _patch_finalizers(monkeypatch, set())
    error = RuntimeError("result construction failed")

    def fail_build_result(*args, **kwargs):
        raise error

    monkeypatch.setattr(runner, "build_run_result", fail_build_result)

    with pytest.raises(RuntimeError) as exc_info:
        runner.run_config(_config([[0]]), RecordingAlgorithm())

    assert exc_info.value is error
    assert events == ["cell", "packet", "run"]


def test_result_serialization_failure_propagates():
    class UnsupportedValue(object):
        pass

    class UnsupportedOutputAlgorithm(Algorithm):
        def execute_cell(self, cell_ctx):
            cell_ctx.push_output("unsupported", UnsupportedValue())

    result = run_config(_config([[0]]), UnsupportedOutputAlgorithm())

    with pytest.raises(TypeError, match="serialized values"):
        result.to_dict()
