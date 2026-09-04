from rm_ref.config import ConfigResolutionError, ConfigResolver, UserConfig
from rm_ref.core import Algorithm, run_config
from rm_ref.schema import SchemaDefinition
from rm_ref.validator import Validator
from rm_ref.runtime.errors import PayloadMappingError
from rm_ref.runtime.result import (
    EXECUTION_ERROR,
    PASS,
    SETUP_ERROR,
    VALIDATION_ERROR,
    OrchestrationResult,
)


def _require_inputs(user_config, schema, algorithm):
    if not isinstance(user_config, UserConfig):
        raise TypeError("user_config must be UserConfig")
    if not isinstance(schema, SchemaDefinition):
        raise TypeError("schema must be SchemaDefinition")
    if not isinstance(algorithm, Algorithm):
        raise TypeError("algorithm must be Algorithm")


def _packet_map(core_config):
    return dict((packet.packet_index, packet) for packet in core_config.packets)


def _cell_indexes(packet):
    return set(cell.cell_index for cell in packet.cells)


def _validate_payload_mapping(core_config, payload_by_packet):
    if payload_by_packet is None:
        return {}
    if not isinstance(payload_by_packet, dict):
        raise PayloadMappingError(
            "payload_by_packet must be a dict or None"
        )

    packets_by_index = _packet_map(core_config)
    for packet_index, cell_mapping in payload_by_packet.items():
        if packet_index not in packets_by_index:
            raise PayloadMappingError(
                "payload contains unknown packet index {0!r}".format(
                    packet_index
                ),
                packet_index=packet_index,
            )
        if not isinstance(cell_mapping, dict):
            raise PayloadMappingError(
                "payload for packet {0!r} must be a dict".format(
                    packet_index
                ),
                packet_index=packet_index,
            )

        known_cells = _cell_indexes(packets_by_index[packet_index])
        for cell_index in cell_mapping:
            if cell_index not in known_cells:
                raise PayloadMappingError(
                    "payload contains unknown cell index {0!r} "
                    "for packet {1!r}".format(cell_index, packet_index),
                    packet_index=packet_index,
                    cell_index=cell_index,
                )
    return payload_by_packet


def _inject_payload(core_config, payload_by_packet):
    payload_by_packet = _validate_payload_mapping(
        core_config,
        payload_by_packet,
    )
    for packet in core_config.packets:
        cell_mapping = payload_by_packet.get(packet.packet_index, {})
        packet.input_pkt_by_cc = {}
        for cell in packet.cells:
            # Runtime retains the caller's validated payload by reference.
            # Core creates the one algorithm-owned copy at CellContext setup.
            packet.input_pkt_by_cc[cell.cell_index] = cell_mapping.get(
                cell.cell_index, []
            )


def run_case(user_config, schema, algorithm, payload_by_packet=None):
    _require_inputs(user_config, schema, algorithm)

    try:
        resolved = ConfigResolver().resolve(user_config, schema=schema)
        validation = Validator(schema).validate(resolved)
        if not validation.ok:
            return OrchestrationResult(
                status=VALIDATION_ERROR,
                validation=validation,
            )

        core_config = resolved.to_core_config()
        _inject_payload(core_config, payload_by_packet)
    except (ConfigResolutionError, PayloadMappingError) as exc:
        return OrchestrationResult(
            status=SETUP_ERROR,
            exception=exc,
        )

    run_result = run_config(core_config, algorithm)
    if run_result.exit_code != 0:
        return OrchestrationResult(
            status=EXECUTION_ERROR,
            validation=validation,
            run_result=run_result,
        )
    return OrchestrationResult(
        status=PASS,
        validation=validation,
        run_result=run_result,
    )
