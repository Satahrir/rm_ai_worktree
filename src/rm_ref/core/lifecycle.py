from copy import deepcopy

from rm_ref.core.context import CellContext, PacketContext, RMContext
from rm_ref.core.errors import FrameworkError, LifecycleFinalizationError


LIFECYCLE_NEW = "NEW"
LIFECYCLE_ACTIVE = "ACTIVE"
LIFECYCLE_FINALIZING = "FINALIZING"
LIFECYCLE_FINALIZED = "FINALIZED"
LIFECYCLE_FINALIZE_FAILED = "FINALIZE_FAILED"


def _get_lifecycle_state(ctx):
    return getattr(ctx, "_lifecycle_state", LIFECYCLE_NEW)


def _set_lifecycle_state(ctx, state):
    ctx._lifecycle_state = state


class FinalizerErrorRecord(object):
    def __init__(self, scope, identity, exception):
        self.scope = scope
        self.identity = identity
        self.exception = exception


class _CleanupItem(object):
    def __init__(self, scope, identity, ctx, finalizer):
        self.scope = scope
        self.identity = identity
        self.ctx = ctx
        self.finalizer = finalizer


class CleanupStack(object):
    def __init__(self):
        self._items = []
        self.finalizer_errors = []

    def push(self, scope, identity, ctx, finalizer):
        state = _get_lifecycle_state(ctx)
        if state != LIFECYCLE_NEW:
            raise FrameworkError(
                "context is already active for scope {0!r}".format(scope)
            )
        _set_lifecycle_state(ctx, LIFECYCLE_ACTIVE)
        self._items.append(
            _CleanupItem(scope, identity, ctx, finalizer)
        )

    def close_through(self, target_ctx):
        found = False
        ok = True
        while self._items:
            item = self._items.pop()
            if not self._close_item(item):
                ok = False
            if item.ctx is target_ctx:
                found = True
                break
        if not found:
            raise FrameworkError("target context is not active")
        return ok

    def close_all_remaining(self):
        ok = True
        while self._items:
            if not self._close_item(self._items.pop()):
                ok = False
        return ok

    def _close_item(self, item):
        state = _get_lifecycle_state(item.ctx)
        if state in (LIFECYCLE_FINALIZED, LIFECYCLE_FINALIZE_FAILED):
            return True
        if state != LIFECYCLE_ACTIVE:
            self.finalizer_errors.append(
                FinalizerErrorRecord(
                    item.scope,
                    item.identity,
                    FrameworkError(
                        "invalid lifecycle state before finalize: {0}".format(
                            state
                        )
                    ),
                )
            )
            return False

        _set_lifecycle_state(item.ctx, LIFECYCLE_FINALIZING)
        try:
            item.finalizer(item.ctx)
        except BaseException as exc:
            _set_lifecycle_state(item.ctx, LIFECYCLE_FINALIZE_FAILED)
            self.finalizer_errors.append(
                FinalizerErrorRecord(item.scope, item.identity, exc)
            )
            return False

        _set_lifecycle_state(item.ctx, LIFECYCLE_FINALIZED)
        return True

    def raise_for_outcome(self, primary_error=None, message=None):
        if not self.finalizer_errors:
            if primary_error is not None:
                raise primary_error
            return

        raise LifecycleFinalizationError(
            message or "lifecycle finalization failed",
            primary_error=primary_error,
            finalizer_errors=self.finalizer_errors,
        )


def _initialize_run_context(rm_ctx, cfg):
    rm_ctx.runtime["config"].update(deepcopy(cfg.global_cfg.parameters))
    rm_ctx.runtime["state"]["packet_count"] = len(cfg.packets)


def _initialize_packet_context(packet_ctx, packet_cfg):
    rm_ctx = packet_ctx.rm_ctx
    packet_ctx.runtime["config"].update(
        deepcopy(rm_ctx.cfg.global_cfg.parameters)
    )
    packet_ctx.runtime["config"].update(deepcopy(packet_cfg.parameters))
    packet_by_cc = {}
    for cell_index, payload in packet_cfg.input_pkt_by_cc.items():
        packet_by_cc[cell_index] = deepcopy(payload)
    for cell_cfg in packet_cfg.cells:
        if cell_cfg.cell_index not in packet_by_cc:
            packet_by_cc[cell_cfg.cell_index] = []
    packet_ctx.runtime["input"]["packet_by_cc"] = packet_by_cc
    packet_ctx.runtime["derived"]["active_cell_indexes"] = [
        cell.cell_index for cell in packet_cfg.cells
    ]
    packet_ctx.runtime["derived"]["active_cell_count"] = len(packet_cfg.cells)


def _initialize_cell_context(cell_ctx, cell_cfg):
    packet_ctx = cell_ctx.packet_ctx
    cell_ctx.runtime["config"].update(
        deepcopy(packet_ctx.rm_ctx.cfg.global_cfg.parameters)
    )
    cell_ctx.runtime["config"].update(
        deepcopy(packet_ctx.packet_cfg.parameters)
    )
    cell_ctx.runtime["config"].update(deepcopy(cell_cfg.parameters))
    cell_ctx.push_input(
        "samples",
        packet_ctx.runtime["input"]["packet_by_cc"][cell_cfg.cell_index],
    )


def prepare_run(cfg):
    rm_ctx = RMContext(cfg)
    rm_ctx._cleanup_stack = CleanupStack()
    rm_ctx._cleanup_stack.push("run", None, rm_ctx, finalize_run)
    try:
        _initialize_run_context(rm_ctx, cfg)
        return rm_ctx
    except BaseException as exc:
        rm_ctx._cleanup_stack.close_all_remaining()
        rm_ctx._cleanup_stack.raise_for_outcome(
            primary_error=exc,
            message="run preparation and cleanup failed",
        )


def prepare_packet(rm_ctx, packet_cfg):
    packet_ctx = PacketContext(rm_ctx, packet_cfg)
    rm_ctx.packet_contexts.append(packet_ctx)
    rm_ctx.packet_context_by_idx[packet_cfg.packet_index] = packet_ctx
    rm_ctx._cleanup_stack.push(
        "packet",
        packet_cfg.packet_index,
        packet_ctx,
        finalize_packet,
    )
    _initialize_packet_context(packet_ctx, packet_cfg)
    return packet_ctx


def prepare_cell(packet_ctx, cell_cfg):
    cell_ctx = CellContext(packet_ctx.rm_ctx, packet_ctx, cell_cfg)
    packet_ctx.cell_contexts.append(cell_ctx)
    packet_ctx.cell_context_by_idx[cell_cfg.cell_index] = cell_ctx
    packet_ctx.rm_ctx._cleanup_stack.push(
        "cell",
        (
            packet_ctx.packet_cfg.packet_index,
            cell_cfg.cell_index,
        ),
        cell_ctx,
        finalize_cell,
    )
    _initialize_cell_context(cell_ctx, cell_cfg)
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
