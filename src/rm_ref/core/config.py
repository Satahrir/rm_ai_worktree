from copy import deepcopy

from rm_ref.core.errors import ConfigError, DuplicateIndexError


def _copy_mapping(value, name):
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError("{0} must be a dict, got {1!r}".format(name, value))
    return deepcopy(value)


def _copy_list(value, name):
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ConfigError("{0} must be a list or tuple, got {1!r}".format(name, value))
    return list(value)


def _normalized_cells(cells, packet_index):
    normalized = []
    seen = set()
    changed = False
    for position, cell in enumerate(cells):
        if not isinstance(cell, CellConfig):
            raise ConfigError(
                "cells[{0}] must be CellConfig, got {1!r}".format(position, cell)
            )
        if cell.cell_index is None:
            # Normalization owns the replacement, not the caller's object.
            cell = CellConfig(cell_index=position, parameters=cell.parameters)
            changed = True
        if cell.cell_index in seen:
            raise DuplicateIndexError(
                "duplicate cell_index {0!r} in packet {1!r}".format(
                    cell.cell_index, packet_index
                )
            )
        seen.add(cell.cell_index)
        normalized.append(cell)
    return normalized, changed


class GlobalConfig(object):
    def __init__(self, parameters=None):
        self.parameters = _copy_mapping(parameters, "global parameters")


class CellConfig(object):
    def __init__(self, cell_index=None, parameters=None):
        self.cell_index = cell_index
        self.parameters = _copy_mapping(parameters, "cell parameters")


class PacketConfig(object):
    def __init__(
        self,
        packet_index=None,
        parameters=None,
        input_pkt_by_cc=None,
        cells=None,
    ):
        self.packet_index = packet_index
        self.parameters = _copy_mapping(parameters, "packet parameters")
        self.input_pkt_by_cc = _copy_mapping(input_pkt_by_cc, "input_pkt_by_cc")
        self.cells = _copy_list(cells, "cells")
        self.normalize_cells()

    def normalize_cells(self):
        self.cells, _ = _normalized_cells(self.cells, self.packet_index)
        return self


class TestcaseConfig(object):
    __test__ = False

    def __init__(self, case_name="", global_cfg=None, packets=None):
        if global_cfg is None:
            global_cfg = GlobalConfig()
        if not isinstance(global_cfg, GlobalConfig):
            raise ConfigError(
                "global_cfg must be GlobalConfig, got {0!r}".format(global_cfg)
            )
        self.case_name = case_name
        self.global_cfg = global_cfg
        self.packets = _copy_list(packets, "packets")
        self.normalize()

    def normalize(self):
        normalized = []
        seen = set()
        for position, packet in enumerate(self.packets):
            if not isinstance(packet, PacketConfig):
                raise ConfigError(
                    "packets[{0}] must be PacketConfig, got {1!r}".format(
                        position, packet
                    )
                )
            packet_index = packet.packet_index
            if packet_index is None:
                packet_index = position
            normalized_cells, cells_changed = _normalized_cells(
                packet.cells, packet_index
            )
            if packet.packet_index is None or cells_changed:
                # Build an owned normalized packet instead of changing the
                # PacketConfig supplied by the caller.
                packet = PacketConfig(
                    packet_index=packet_index,
                    parameters=packet.parameters,
                    input_pkt_by_cc=packet.input_pkt_by_cc,
                    cells=normalized_cells,
                )
            if packet_index in seen:
                raise DuplicateIndexError(
                    "duplicate packet_index {0!r}".format(packet_index)
                )
            seen.add(packet_index)
            normalized.append(packet)
        self.packets = normalized
        return self
