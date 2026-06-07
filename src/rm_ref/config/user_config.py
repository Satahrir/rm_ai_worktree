from copy import deepcopy

from rm_ref.config.errors import ConfigError


def _copy_mapping(value, label):
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError("{0} must be a dict, got {1!r}".format(label, value))
    return deepcopy(value)


def _copy_sequence(value, label):
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ConfigError(
            "{0} must be a list or tuple, got {1!r}".format(label, value)
        )
    return list(value)


class UserCellConfig(object):
    def __init__(self, cell_index=None, values=None):
        self.cell_index = cell_index
        self.values = _copy_mapping(values, "cell values")

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ConfigError("cell config must be a dict, got {0!r}".format(data))
        return cls(
            cell_index=data.get("cell_index"),
            values=data.get("values"),
        )


class UserPacketConfig(object):
    def __init__(self, packet_index=None, values=None, cells=None):
        self.packet_index = packet_index
        self.values = _copy_mapping(values, "packet values")
        self.cells = _copy_sequence(cells, "packet cells")
        normalized_cells = []
        for position, cell in enumerate(self.cells):
            if isinstance(cell, dict):
                cell = UserCellConfig.from_dict(cell)
            if not isinstance(cell, UserCellConfig):
                raise ConfigError(
                    "cells[{0}] must be UserCellConfig or dict, got {1!r}".format(
                        position, cell
                    )
                )
            normalized_cells.append(cell)
        self.cells = normalized_cells

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ConfigError(
                "packet config must be a dict, got {0!r}".format(data)
            )
        return cls(
            packet_index=data.get("packet_index"),
            values=data.get("values"),
            cells=data.get("cells"),
        )


class UserConfig(object):
    def __init__(
        self,
        case_name="",
        algorithm_name="",
        schema_id=None,
        global_values=None,
        packets=None,
    ):
        self.case_name = case_name
        self.algorithm_name = algorithm_name
        self.schema_id = schema_id
        self.global_values = _copy_mapping(global_values, "global values")
        self.packets = _copy_sequence(packets, "packets")
        normalized_packets = []
        for position, packet in enumerate(self.packets):
            if isinstance(packet, dict):
                packet = UserPacketConfig.from_dict(packet)
            if not isinstance(packet, UserPacketConfig):
                raise ConfigError(
                    "packets[{0}] must be UserPacketConfig or dict, got {1!r}".format(
                        position, packet
                    )
                )
            normalized_packets.append(packet)
        self.packets = normalized_packets

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ConfigError("user config must be a dict, got {0!r}".format(data))
        return cls(
            case_name=data.get("case_name", ""),
            algorithm_name=data.get("algorithm_name", ""),
            schema_id=data.get("schema_id"),
            global_values=data.get("global_values"),
            packets=data.get("packets"),
        )
