from copy import deepcopy

from rm_ref.config.errors import ConfigError


def _copy_mapping(value, label):
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError("{0} must be a dict, got {1!r}".format(label, value))
    return deepcopy(value)


class ResolvedCellConfig(object):
    def __init__(self, cell_index, values=None, value_sources=None):
        self.cell_index = cell_index
        self.values = _copy_mapping(values, "resolved cell values")
        self.value_sources = _copy_mapping(
            value_sources, "resolved cell value sources"
        )


class ResolvedPacketConfig(object):
    def __init__(
        self,
        packet_index,
        values=None,
        value_sources=None,
        cells=None,
    ):
        self.packet_index = packet_index
        self.values = _copy_mapping(values, "resolved packet values")
        self.value_sources = _copy_mapping(
            value_sources, "resolved packet value sources"
        )
        self.cells = list(cells or [])
        for position, cell in enumerate(self.cells):
            if not isinstance(cell, ResolvedCellConfig):
                raise ConfigError(
                    "resolved cells[{0}] must be ResolvedCellConfig, got {1!r}".format(
                        position, cell
                    )
                )


class ResolvedConfig(object):
    def __init__(
        self,
        case_name,
        algorithm_name,
        schema_id,
        global_values=None,
        global_value_sources=None,
        packets=None,
    ):
        self.case_name = case_name
        self.algorithm_name = algorithm_name
        self.schema_id = schema_id
        self.global_values = _copy_mapping(
            global_values, "resolved global values"
        )
        self.global_value_sources = _copy_mapping(
            global_value_sources, "resolved global value sources"
        )
        self.packets = list(packets or [])
        for position, packet in enumerate(self.packets):
            if not isinstance(packet, ResolvedPacketConfig):
                raise ConfigError(
                    "resolved packets[{0}] must be ResolvedPacketConfig, "
                    "got {1!r}".format(position, packet)
                )

    def to_core_config(self):
        from rm_ref.core.config import (
            CellConfig,
            GlobalConfig,
            PacketConfig,
            TestcaseConfig,
        )

        global_parameters = deepcopy(self.global_values)
        if self.algorithm_name:
            global_parameters.setdefault("algorithm_name", self.algorithm_name)
        packets = []
        for packet in self.packets:
            cells = [
                CellConfig(
                    cell_index=cell.cell_index,
                    parameters=cell.values,
                )
                for cell in packet.cells
            ]
            packets.append(
                PacketConfig(
                    packet_index=packet.packet_index,
                    parameters=packet.values,
                    cells=cells,
                )
            )
        return TestcaseConfig(
            case_name=self.case_name,
            global_cfg=GlobalConfig(parameters=global_parameters),
            packets=packets,
        )
