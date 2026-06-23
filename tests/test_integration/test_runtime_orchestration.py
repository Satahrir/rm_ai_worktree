from copy import deepcopy

import pytest

from rm_ref.config import ConfigResolutionError, UserConfig
from rm_ref.core import Algorithm, FrameworkError
from rm_ref.runtime import (
    EXECUTION_ERROR,
    PASS,
    SETUP_ERROR,
    VALIDATION_ERROR,
    OrchestrationResult,
    PayloadMappingError,
    run_case,
)
import rm_ref.runtime.runner as runtime_runner
from rm_ref.schema import SchemaDefinition


def make_schema(schema_id="runtime/v1"):
    return SchemaDefinition.from_dict(
        {
            "schema_id": schema_id,
            "word_width": 8,
            "word_count": 2,
            "fields": [
                {
                    "name": "run_mode",
                    "scope": "global",
                    "enum": {"FAST": 1, "SAFE": 2},
                    "default": "SAFE",
                },
                {
                    "name": "packet_kind",
                    "scope": "packet",
                    "required": True,
                    "enum": {"DATA": 3, "CTRL": 4},
                    "word": 0,
                    "msb": 3,
                    "lsb": 0,
                },
                {
                    "name": "cell_gain",
                    "scope": "cell",
                    "default": 5,
                    "min": 1,
                    "max": 10,
                    "word": 1,
                    "msb": 3,
                    "lsb": 0,
                },
                {
                    "name": "cell_flag",
                    "scope": "cell",
                    "enum": {"OFF": 0, "ON": 1},
                    "default": "ON",
                    "word": 1,
                    "msb": 4,
                    "lsb": 4,
                },
            ],
        }
    )


def make_user_config(schema_id="runtime/v1", cell_values=None):
    return UserConfig.from_dict(
        {
            "case_name": "runtime-case",
            "algorithm_name": "business-name",
            "schema_id": schema_id,
            "packets": [
                {
                    "packet_index": 2,
                    "values": {"packet_kind": "CTRL"},
                    "cells": [
                        {
                            "cell_index": 7,
                            "values": cell_values or {},
                        }
                    ],
                }
            ],
        }
    )


class RecordingAlgorithm(Algorithm):
    def __init__(self):
        self.calls = []

    def execute_cell(self, cell_ctx):
        samples = cell_ctx.get_input("samples", [])
        self.calls.append(
            {
                "packet_index": cell_ctx.packet_ctx.packet_cfg.packet_index,
                "cell_index": cell_ctx.cell_cfg.cell_index,
                "samples": deepcopy(samples),
                "run_mode": cell_ctx.get_config("run_mode"),
                "packet_kind": cell_ctx.get_config("packet_kind"),
                "cell_gain": cell_ctx.get_config("cell_gain"),
                "cell_flag": cell_ctx.get_config("cell_flag"),
            }
        )
        cell_ctx.push_output("sample_count", len(samples))
        cell_ctx.push_output("run_mode", cell_ctx.get_config("run_mode"))
        cell_ctx.push_output("packet_kind", cell_ctx.get_config("packet_kind"))
        cell_ctx.push_output("cell_gain", cell_ctx.get_config("cell_gain"))
        cell_ctx.push_output("cell_flag", cell_ctx.get_config("cell_flag"))


class MutatingAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        samples = cell_ctx.get_input("samples", [])
        samples.append("changed")
        cell_ctx.push_output("samples", samples)


class ReportedErrorAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        cell_ctx.error("BAD_PAYLOAD", "payload was rejected")


class FailingAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        raise RuntimeError("algorithm failed")


class FrameworkFailingAlgorithm(Algorithm):
    def execute_cell(self, cell_ctx):
        raise FrameworkError("framework failed")


def test_valid_schema_user_config_and_payload_execute_through_core():
    algorithm = RecordingAlgorithm()
    result = run_case(
        make_user_config(),
        make_schema(),
        algorithm,
        payload_by_packet={2: {7: [10, 20, 30]}},
    )

    assert result.status == PASS
    assert result.validation.ok
    assert result.run_result.exit_code == 0
    assert algorithm.calls == [
        {
            "packet_index": 2,
            "cell_index": 7,
            "samples": [10, 20, 30],
            "run_mode": 2,
            "packet_kind": 4,
            "cell_gain": 5,
            "cell_flag": 1,
        }
    ]
    cell_output = result.run_result.packet_outputs[0].cell_outputs[0]
    assert cell_output.output["sample_count"] == 3


def test_schema_defaults_and_enum_conversion_are_visible_to_algorithm():
    algorithm = RecordingAlgorithm()
    result = run_case(make_user_config(), make_schema(), algorithm)

    assert result.status == PASS
    assert algorithm.calls[0]["samples"] == []
    assert algorithm.calls[0]["run_mode"] == 2
    assert algorithm.calls[0]["packet_kind"] == 4
    assert algorithm.calls[0]["cell_gain"] == 5
    assert algorithm.calls[0]["cell_flag"] == 1


def test_validation_errors_prevent_core_execution(monkeypatch):
    algorithm = RecordingAlgorithm()

    def fail_if_called(core_config, injected_algorithm):
        raise AssertionError("core.run_config must not be called")

    monkeypatch.setattr(runtime_runner, "run_config", fail_if_called)

    result = run_case(
        make_user_config(cell_values={"cell_gain": 99}),
        make_schema(),
        algorithm,
    )

    assert result.status == VALIDATION_ERROR
    assert not result.validation.ok
    assert result.run_result is None
    assert algorithm.calls == []


def test_schema_id_mismatch_returns_setup_error():
    result = run_case(
        make_user_config(schema_id="other/v1"),
        make_schema(),
        RecordingAlgorithm(),
    )

    assert result.status == SETUP_ERROR
    assert isinstance(result.exception, ConfigResolutionError)
    assert result.run_result is None


def test_extra_packet_payload_returns_setup_error():
    result = run_case(
        make_user_config(),
        make_schema(),
        RecordingAlgorithm(),
        payload_by_packet={99: {}},
    )

    assert result.status == SETUP_ERROR
    assert isinstance(result.exception, PayloadMappingError)
    assert result.exception.packet_index == 99


def test_extra_cell_payload_returns_setup_error():
    result = run_case(
        make_user_config(),
        make_schema(),
        RecordingAlgorithm(),
        payload_by_packet={2: {99: []}},
    )

    assert result.status == SETUP_ERROR
    assert isinstance(result.exception, PayloadMappingError)
    assert result.exception.packet_index == 2
    assert result.exception.cell_index == 99


def test_invalid_payload_mapping_shape_returns_setup_error():
    outer_result = run_case(
        make_user_config(),
        make_schema(),
        RecordingAlgorithm(),
        payload_by_packet=[],
    )
    inner_result = run_case(
        make_user_config(),
        make_schema(),
        RecordingAlgorithm(),
        payload_by_packet={2: []},
    )

    assert outer_result.status == SETUP_ERROR
    assert isinstance(outer_result.exception, PayloadMappingError)
    assert inner_result.status == SETUP_ERROR
    assert isinstance(inner_result.exception, PayloadMappingError)


def test_missing_payload_entries_become_empty_samples():
    algorithm = RecordingAlgorithm()

    result = run_case(
        make_user_config(),
        make_schema(),
        algorithm,
        payload_by_packet={},
    )

    assert result.status == PASS
    assert algorithm.calls[0]["samples"] == []
    assert result.run_result.packet_outputs[0].cell_outputs[0].output[
        "sample_count"
    ] == 0


def test_caller_payload_is_not_mutated():
    payload = {2: {7: ["original"]}}
    original = deepcopy(payload)

    result = run_case(
        make_user_config(),
        make_schema(),
        MutatingAlgorithm(),
        payload_by_packet=payload,
    )

    assert result.status == PASS
    assert payload == original
    assert result.run_result.packet_outputs[0].cell_outputs[0].output[
        "samples"
    ] == ["original", "changed"]


def test_algorithm_reported_error_becomes_execution_error():
    result = run_case(
        make_user_config(),
        make_schema(),
        ReportedErrorAlgorithm(),
    )

    assert result.status == EXECUTION_ERROR
    assert result.exception is None
    assert result.run_result.exit_code == 1
    assert result.run_result.errors[0].code == "BAD_PAYLOAD"


def test_algorithm_exception_captured_by_core_becomes_execution_error():
    result = run_case(make_user_config(), make_schema(), FailingAlgorithm())

    assert result.status == EXECUTION_ERROR
    assert result.exception is None
    assert result.run_result.exit_code == 1
    assert isinstance(result.run_result.exception, RuntimeError)


def test_core_framework_exception_propagates():
    with pytest.raises(FrameworkError, match="framework failed"):
        run_case(make_user_config(), make_schema(), FrameworkFailingAlgorithm())


def test_non_schema_and_non_algorithm_inputs_propagate_type_error():
    with pytest.raises(TypeError, match="schema must be SchemaDefinition"):
        run_case(make_user_config(), object(), RecordingAlgorithm())

    with pytest.raises(TypeError, match="algorithm must be Algorithm"):
        run_case(make_user_config(), make_schema(), object())


def test_orchestration_result_to_dict_emits_plain_deterministic_data():
    result = run_case(
        make_user_config(),
        make_schema(),
        RecordingAlgorithm(),
        payload_by_packet={2: {7: [1, 2]}},
    )

    serialized = result.to_dict()

    assert serialized["status"] == PASS
    assert serialized["validation"] == {
        "ok": True,
        "errors": [],
        "warnings": [],
    }
    assert serialized["run_result"]["exit_code"] == 0
    assert serialized["run_result"]["packet_outputs"][0]["cell_outputs"][0][
        "output"
    ]["sample_count"] == 2
    assert serialized["exception"] is None


def test_setup_error_to_dict_includes_expected_exception_metadata():
    result = run_case(
        make_user_config(),
        make_schema(),
        RecordingAlgorithm(),
        payload_by_packet={2: {99: []}},
    )

    assert result.to_dict()["exception"] == {
        "type": "PayloadMappingError",
        "message": "payload contains unknown cell index 99 for packet 2",
        "packet_index": 2,
        "cell_index": 99,
    }


def test_manual_orchestration_result_rejects_invalid_status():
    with pytest.raises(ValueError, match="invalid orchestration status"):
        OrchestrationResult("BROKEN")
