import pytest

from rm_ref.core.config import (
    CellConfig,
    GlobalConfig,
    PacketConfig,
    TestcaseConfig,
)
from rm_ref.core.errors import DuplicateIndexError
from rm_ref.core.lifecycle import build_context_tree


def test_config_constructs_testcase_packet_cell():
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
    assert cfg.packets[0].packet_index == 4
    assert cfg.packets[0].cells[0].cell_index == 3


def test_packet_normalize_assigns_indexes():
    cfg = TestcaseConfig(
        packets=[
            PacketConfig(cells=[CellConfig(), CellConfig()]),
            PacketConfig(cells=[CellConfig()]),
        ]
    )

    assert [packet.packet_index for packet in cfg.packets] == [0, 1]
    assert [cell.cell_index for cell in cfg.packets[0].cells] == [0, 1]
    assert [cell.cell_index for cell in cfg.packets[1].cells] == [0]


def test_duplicate_indexes_are_rejected():
    with pytest.raises(DuplicateIndexError, match="duplicate cell_index 2"):
        PacketConfig(cells=[CellConfig(2), CellConfig(2)])

    with pytest.raises(DuplicateIndexError, match="duplicate packet_index 5"):
        TestcaseConfig(
            packets=[PacketConfig(5), PacketConfig(5)]
        )


def test_context_tree_is_created_and_runtime_is_prepared():
    cfg = TestcaseConfig(
        global_cfg=GlobalConfig({"global_value": 1}),
        packets=[
            PacketConfig(
                parameters={"packet_value": 2},
                input_pkt_by_cc={0: [4, 5]},
                cells=[CellConfig(parameters={"cell_value": 3})],
            )
        ],
    )

    rm_ctx = build_context_tree(cfg)
    packet_ctx = rm_ctx.packet_contexts[0]
    cell_ctx = packet_ctx.cell_contexts[0]

    assert rm_ctx.packet_context_by_idx[0] is packet_ctx
    assert packet_ctx.cell_context_by_idx[0] is cell_ctx
    assert packet_ctx.get_derived("active_cell_count") == 1
    assert cell_ctx.get_config("global_value") == 1
    assert cell_ctx.get_config("packet_value") == 2
    assert cell_ctx.get_config("cell_value") == 3
    assert cell_ctx.get_input("samples") == [4, 5]


def test_missing_cell_input_becomes_empty_list():
    cfg = TestcaseConfig(
        packets=[PacketConfig(cells=[CellConfig(cell_index=7)])]
    )

    cell_ctx = build_context_tree(cfg).packet_contexts[0].cell_contexts[0]

    assert cell_ctx.get_input("samples") == []
