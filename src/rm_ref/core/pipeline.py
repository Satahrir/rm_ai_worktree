from rm_ref.core.lifecycle import (
    finalize_cell,
    finalize_packet,
    finalize_run,
    prepare_cell,
    prepare_packet,
)


ALGORITHM_EXCEPTION = "ALGORITHM_EXCEPTION"


def execute_pipeline(rm_ctx, algorithm):
    for packet_cfg in rm_ctx.cfg.packets:
        packet_ctx = prepare_packet(rm_ctx, packet_cfg)
        for cell_cfg in packet_cfg.cells:
            cell_ctx = prepare_cell(packet_ctx, cell_cfg)
            try:
                algorithm.execute_cell(cell_ctx)
            except Exception as exc:
                cell_ctx.error(
                    ALGORITHM_EXCEPTION,
                    "algorithm raised {0}: {1}".format(
                        exc.__class__.__name__, exc
                    ),
                    exception_type=exc.__class__.__name__,
                )
                raise
            finally:
                finalize_cell(cell_ctx)
        finalize_packet(packet_ctx)
    finalize_run(rm_ctx)
    return rm_ctx
