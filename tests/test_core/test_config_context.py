import pytest


config_module = pytest.importorskip(
    "rm_ref.core.config",
    reason="Core Agent must implement rm_ref.core.config before config tests can run",
)
context_module = pytest.importorskip(
    "rm_ref.core.context",
    reason="Core Agent must implement rm_ref.core.context before context tests can run",
)

CellConfig = config_module.CellConfig
PacketConfig = config_module.PacketConfig
TestcaseConfig = config_module.TestcaseConfig
RMContext = context_module.RMContext


def test_config_constructs_testcase_packet_and_cell():
    cell = CellConfig(cell_index=4, parameters={"gain": 3})
    packet = PacketConfig(
        packet_index=2,
        parameters={"mode": "loopback"},
        input_pkt_by_cc={4: [10, 20]},
        cells=[cell],
    )
    cfg = TestcaseConfig(
        case_name="construction",
        global_cfg={"seed": 17},
        packets=[packet],
    )

    assert cfg.case_name == "construction"
    assert cfg.global_cfg == {"seed": 17}
    assert cfg.packets == [packet]
    assert packet.parameters == {"mode": "loopback"}
    assert packet.input_pkt_by_cc == {4: [10, 20]}
    assert packet.cells == [cell]
    assert cell.parameters == {"gain": 3}


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


def test_context_tree_preserves_config_links_and_parent_links():
    cfg = TestcaseConfig(
        case_name="context-tree",
        packets=[
            PacketConfig(
                cells=[
                    CellConfig(parameters={"cell": "a"}),
                    CellConfig(parameters={"cell": "b"}),
                ]
            )
        ],
    )

    rm_ctx = RMContext(cfg)

    assert rm_ctx.cfg is cfg
    assert len(rm_ctx.packet_contexts) == 1

    packet_ctx = rm_ctx.packet_contexts[0]
    assert packet_ctx.rm_ctx is rm_ctx
    assert packet_ctx.packet_cfg is cfg.packets[0]
    assert len(packet_ctx.cell_contexts) == 2
    assert packet_ctx.cell_context_by_idx[0] is packet_ctx.cell_contexts[0]
    assert packet_ctx.cell_context_by_idx[1] is packet_ctx.cell_contexts[1]

    cell_ctx = packet_ctx.cell_contexts[1]
    assert cell_ctx.rm_ctx is rm_ctx
    assert cell_ctx.packet_ctx is packet_ctx
    assert cell_ctx.cell_cfg is cfg.packets[0].cells[1]
