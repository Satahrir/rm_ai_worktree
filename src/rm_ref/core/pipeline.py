from rm_ref.core.errors import (
    AlgorithmExecutionError,
    DiagnosticRecordingError,
    FrameworkError,
)
from rm_ref.core.lifecycle import (
    prepare_cell,
    prepare_packet,
)


ALGORITHM_EXCEPTION = "ALGORITHM_EXCEPTION"


class _StopBusinessTraversal(Exception):
    pass


def _algorithm_name(algorithm):
    return algorithm.__class__.__name__


def _execute_algorithm_cell(cell_ctx, algorithm, algorithm_name):
    packet_index = cell_ctx.packet_ctx.packet_cfg.packet_index
    cell_index = cell_ctx.cell_cfg.cell_index
    try:
        algorithm.execute_cell(cell_ctx)
    except FrameworkError:
        raise
    except Exception as exc:
        try:
            cell_ctx.error(
                ALGORITHM_EXCEPTION,
                "algorithm raised {0}: {1}".format(
                    exc.__class__.__name__, exc
                ),
                exception_type=exc.__class__.__name__,
            )
        except Exception as recording_error:
            raise DiagnosticRecordingError(
                "failed to record algorithm exception diagnostic",
                primary_error=exc,
                recording_error=recording_error,
            )
        raise AlgorithmExecutionError(
            "algorithm execution failed",
            original_exception=exc,
            packet_index=packet_index,
            cell_index=cell_index,
            algorithm_name=algorithm_name,
        )


def _run_cell(packet_ctx, cell_cfg, algorithm, algorithm_name):
    cleanup_stack = packet_ctx.rm_ctx._cleanup_stack
    cell_ctx = prepare_cell(packet_ctx, cell_cfg)
    primary_error = None
    try:
        _execute_algorithm_cell(cell_ctx, algorithm, algorithm_name)
    except BaseException as exc:
        primary_error = exc

    finalize_ok = cleanup_stack.close_through(cell_ctx)
    if primary_error is not None:
        raise primary_error
    if not finalize_ok:
        raise _StopBusinessTraversal()


def _run_packet(rm_ctx, packet_cfg, algorithm, algorithm_name):
    cleanup_stack = rm_ctx._cleanup_stack
    packet_ctx = prepare_packet(rm_ctx, packet_cfg)
    primary_error = None
    traversal_stopped = False
    try:
        for cell_cfg in packet_cfg.cells:
            _run_cell(packet_ctx, cell_cfg, algorithm, algorithm_name)
    except _StopBusinessTraversal:
        traversal_stopped = True
    except BaseException as exc:
        primary_error = exc

    finalize_ok = cleanup_stack.close_through(packet_ctx)
    if primary_error is not None:
        raise primary_error
    if traversal_stopped or not finalize_ok:
        raise _StopBusinessTraversal()


def execute_pipeline(rm_ctx, algorithm):
    cleanup_stack = rm_ctx._cleanup_stack
    algorithm_name = _algorithm_name(algorithm)
    primary_error = None
    try:
        for packet_cfg in rm_ctx.cfg.packets:
            _run_packet(rm_ctx, packet_cfg, algorithm, algorithm_name)
    except _StopBusinessTraversal:
        pass
    except BaseException as exc:
        primary_error = exc
    finally:
        cleanup_stack.close_all_remaining()

    cleanup_stack.raise_for_outcome(primary_error=primary_error)
    return rm_ctx
