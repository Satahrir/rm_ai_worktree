from copy import deepcopy

from rm_ref.core.context import CellContext, PacketContext, RMContext


def prepare_run(cfg):
    rm_ctx = RMContext(cfg)
    rm_ctx.runtime["config"].update(deepcopy(cfg.global_cfg.parameters))
    rm_ctx.runtime["state"]["packet_count"] = len(cfg.packets)
    return rm_ctx


def prepare_packet(rm_ctx, packet_cfg):
    packet_ctx = PacketContext(rm_ctx, packet_cfg)
    packet_ctx.runtime["config"].update(
        deepcopy(rm_ctx.cfg.global_cfg.parameters)
    )
    packet_ctx.runtime["config"].update(deepcopy(packet_cfg.parameters))
    packet_ctx.runtime["input"]["packet_by_cc"] = deepcopy(
        packet_cfg.input_pkt_by_cc
    )
    packet_ctx.runtime["derived"]["active_cell_indexes"] = [
        cell.cell_index for cell in packet_cfg.cells
    ]
    packet_ctx.runtime["derived"]["active_cell_count"] = len(packet_cfg.cells)

    rm_ctx.packet_contexts.append(packet_ctx)
    rm_ctx.packet_context_by_idx[packet_cfg.packet_index] = packet_ctx
    return packet_ctx


def prepare_cell(packet_ctx, cell_cfg):
    cell_ctx = CellContext(packet_ctx.rm_ctx, packet_ctx, cell_cfg)
    cell_ctx.runtime["config"].update(
        deepcopy(packet_ctx.rm_ctx.cfg.global_cfg.parameters)
    )
    cell_ctx.runtime["config"].update(
        deepcopy(packet_ctx.packet_cfg.parameters)
    )
    cell_ctx.runtime["config"].update(deepcopy(cell_cfg.parameters))
    cell_ctx.push_input(
        "samples",
        deepcopy(
            packet_ctx.packet_cfg.input_pkt_by_cc.get(cell_cfg.cell_index, [])
        ),
    )

    packet_ctx.cell_contexts.append(cell_ctx)
    packet_ctx.cell_context_by_idx[cell_cfg.cell_index] = cell_ctx
    return cell_ctx


def finalize_cell(cell_ctx):
    cell_ctx.runtime["state"]["completed"] = True


def finalize_packet(packet_ctx):
    packet_ctx.runtime["state"]["completed"] = True
    packet_ctx.runtime["state"]["executed_cell_count"] = len(
        packet_ctx.cell_contexts
    )


def finalize_run(rm_ctx):
    rm_ctx.runtime["state"]["completed"] = True
    rm_ctx.runtime["state"]["executed_packet_count"] = len(
        rm_ctx.packet_contexts
    )


def build_context_tree(cfg):
    rm_ctx = prepare_run(cfg)
    for packet_cfg in cfg.packets:
        packet_ctx = prepare_packet(rm_ctx, packet_cfg)
        for cell_cfg in packet_cfg.cells:
            prepare_cell(packet_ctx, cell_cfg)
    return rm_ctx
