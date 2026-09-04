import pytest

from rm_ref.core.config import (
    CellConfig,
    GlobalConfig,
    PacketConfig,
    TestcaseConfig,
)
from rm_ref.core.context import RMContext
from rm_ref.core.errors import DuplicateIndexError
from rm_ref.core.lifecycle import build_context_tree


def test_config_constructs_testcase_packet_and_cell():
    cell = CellConfig(cell_index=3, parameters={"gain": 2})
    packet = PacketConfig(
        packet_index=4,
        parameters={"mode": "test"},
        input_pkt_by_cc={3: [10, 20]},
        cells=[cell],
    )
    cfg = TestcaseConfig(
        case_name="basic",
        global_cfg=GlobalConfig({"seed": 9}),
        packets=[packet],
    )

    assert cfg.case_name == "basic"
    assert cfg.global_cfg.parameters == {"seed": 9}
    assert cfg.packets == [packet]
    assert packet.parameters == {"mode": "test"}
    assert packet.input_pkt_by_cc == {3: [10, 20]}
    assert packet.cells == [cell]
    assert cell.parameters == {"gain": 2}


def test_config_normalizes_packet_and_cell_indexes_from_list_order():
    cfg = TestcaseConfig(
        case_name="normalized",
        packets=[
            PacketConfig(cells=[CellConfig(), CellConfig()]),
            PacketConfig(cells=[CellConfig()]),
        ],
    )

    assert [packet.packet_index for packet in cfg.packets] == [0, 1]
    assert [cell.cell_index for cell in cfg.packets[0].cells] == [0, 1]
    assert [cell.cell_index for cell in cfg.packets[1].cells] == [0]


def test_packet_normalization_does_not_mutate_caller_cell():
    caller_cell = CellConfig(parameters={"gain": 3})

    packet = PacketConfig(cells=[caller_cell])

    assert caller_cell.cell_index is None
    assert packet.cells[0] is not caller_cell
    assert packet.cells[0].cell_index == 0
    assert packet.cells[0].parameters == {"gain": 3}


def test_testcase_normalization_does_not_mutate_caller_packet():
    caller_packet = PacketConfig(parameters={"mode": "test"})

    cfg = TestcaseConfig(packets=[caller_packet])

    assert caller_packet.packet_index is None
    assert cfg.packets[0] is not caller_packet
    assert cfg.packets[0].packet_index == 0
    assert cfg.packets[0].parameters == {"mode": "test"}


def test_duplicate_indexes_are_rejected():
    with pytest.raises(DuplicateIndexError, match="duplicate cell_index 2"):
        PacketConfig(cells=[CellConfig(2), CellConfig(2)])

    with pytest.raises(DuplicateIndexError, match="duplicate packet_index 5"):
        TestcaseConfig(packets=[PacketConfig(5), PacketConfig(5)])


def test_rm_context_declares_cleanup_stack_attribute():
    rm_ctx = RMContext(TestcaseConfig())

    assert rm_ctx._cleanup_stack is None


def test_context_tree_preserves_links_and_prepares_runtime():
    cfg = TestcaseConfig(
        case_name="context-tree",
        global_cfg=GlobalConfig({"global_value": 1}),
        packets=[
            PacketConfig(
                parameters={"packet_value": 2},
                input_pkt_by_cc={0: [4, 5]},
                cells=[
                    CellConfig(parameters={"cell_value": 3}),
                    CellConfig(parameters={"cell_value": 4}),
                ],
            )
        ],
    )

    rm_ctx = build_context_tree(cfg)
    packet_ctx = rm_ctx.packet_contexts[0]
    cell_ctx = packet_ctx.cell_contexts[1]

    assert rm_ctx.cfg is cfg
    assert rm_ctx.packet_context_by_idx[0] is packet_ctx
    assert packet_ctx.rm_ctx is rm_ctx
    assert packet_ctx.packet_cfg is cfg.packets[0]
    assert packet_ctx.cell_context_by_idx[1] is cell_ctx
    assert packet_ctx.get_derived("active_cell_count") == 2
    assert cell_ctx.rm_ctx is rm_ctx
    assert cell_ctx.packet_ctx is packet_ctx
    assert cell_ctx.cell_cfg is cfg.packets[0].cells[1]
    assert cell_ctx.get_config("global_value") == 1
    assert cell_ctx.get_config("packet_value") == 2
    assert cell_ctx.get_config("cell_value") == 4


def test_context_tree_maps_input_by_cell_and_defaults_to_empty_list():
    cfg = TestcaseConfig(
        packets=[
            PacketConfig(
                input_pkt_by_cc={0: [4, 5]},
                cells=[CellConfig(), CellConfig(cell_index=7)],
            )
        ],
    )

    cell_contexts = build_context_tree(cfg).packet_contexts[0].cell_contexts

    assert cell_contexts[0].get_input("samples") == [4, 5]
    assert cell_contexts[1].get_input("samples") == []


def test_packet_context_references_payload_and_cell_context_owns_isolated_copy():
    samples = [{"value": 4}]
    packet = PacketConfig(
        input_pkt_by_cc={0: samples},
        cells=[CellConfig()],
    )

    rm_ctx = build_context_tree(TestcaseConfig(packets=[packet]))
    packet_ctx = rm_ctx.packet_contexts[0]
    cell_samples = packet_ctx.cell_contexts[0].get_input("samples")

    assert (
        packet_ctx.get_input("packet_by_cc")
        is packet_ctx.packet_cfg.input_pkt_by_cc
    )
    assert cell_samples == samples
    assert cell_samples is not samples
    assert cell_samples[0] is not samples[0]


def test_config_snapshot_is_detached_from_context_runtime():
    cfg = TestcaseConfig(
        global_cfg=GlobalConfig({"nested": {"value": 1}}),
        packets=[PacketConfig(cells=[CellConfig()])],
    )
    cell_ctx = build_context_tree(cfg).packet_contexts[0].cell_contexts[0]

    snapshot = cell_ctx.get_config_snapshot()
    snapshot["nested"]["value"] = 9

    assert cell_ctx.get_config("nested") == {"value": 1}
