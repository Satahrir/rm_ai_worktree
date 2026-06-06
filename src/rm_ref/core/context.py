from rm_ref.core.diagnostic import (
    DEBUG,
    ERROR as DIAGNOSTIC_ERROR,
    TRACE,
    WARNING as DIAGNOSTIC_WARNING,
    Diagnostic,
)
from rm_ref.core.status import ERROR, OK, WARNING, combine_status


RUNTIME_SCOPES = ("state", "config", "derived", "input", "output", "trace")


class _RuntimeContext(object):
    def __init__(self):
        self.runtime = dict((scope, {}) for scope in RUNTIME_SCOPES)
        self.warnings = []
        self.errors = []
        self.debug_logs = []
        self.trace = []
        self.status = OK

    def _packet_index(self):
        return None

    def _cell_index(self):
        return None

    def _parent_context(self):
        return None

    def _record(self, diagnostic, propagate=True):
        if diagnostic.severity == DIAGNOSTIC_WARNING:
            self.warnings.append(diagnostic)
            self.status = combine_status(self.status, WARNING)
        elif diagnostic.severity == DIAGNOSTIC_ERROR:
            self.errors.append(diagnostic)
            self.status = combine_status(self.status, ERROR)
        elif diagnostic.severity == DEBUG:
            self.debug_logs.append(diagnostic)
        elif diagnostic.severity == TRACE:
            self.trace.append(diagnostic)

        parent = self._parent_context()
        if propagate and parent is not None:
            parent._record(diagnostic, propagate=True)
        return diagnostic

    def warn(self, code, message, **fields):
        return self._record(
            Diagnostic(
                DIAGNOSTIC_WARNING,
                code,
                message,
                self._packet_index(),
                self._cell_index(),
                fields,
            )
        )

    def error(self, code, message, **fields):
        return self._record(
            Diagnostic(
                DIAGNOSTIC_ERROR,
                code,
                message,
                self._packet_index(),
                self._cell_index(),
                fields,
            )
        )

    def debug(self, message, **fields):
        return self._record(
            Diagnostic(
                DEBUG,
                "DEBUG",
                message,
                self._packet_index(),
                self._cell_index(),
                fields,
            )
        )

    def trace_event(self, message, **fields):
        return self._record(
            Diagnostic(
                TRACE,
                "TRACE",
                message,
                self._packet_index(),
                self._cell_index(),
                fields,
            )
        )

    def set_runtime(self, scope, key, value):
        if scope not in self.runtime:
            raise KeyError("unknown runtime scope: {0!r}".format(scope))
        self.runtime[scope][key] = value

    def get_runtime(self, scope, key, default=None):
        if scope not in self.runtime:
            raise KeyError("unknown runtime scope: {0!r}".format(scope))
        return self.runtime[scope].get(key, default)

    def push_input(self, key, value):
        self.set_runtime("input", key, value)

    def get_input(self, key, default=None):
        return self.get_runtime("input", key, default)

    def push_output(self, key, value):
        self.set_runtime("output", key, value)

    def get_output(self, key, default=None):
        return self.get_runtime("output", key, default)

    def push_derived(self, key, value):
        self.set_runtime("derived", key, value)

    def get_derived(self, key, default=None):
        return self.get_runtime("derived", key, default)

    def get_config(self, key, default=None):
        return self.get_runtime("config", key, default)


class RMContext(_RuntimeContext):
    def __init__(self, cfg):
        _RuntimeContext.__init__(self)
        self.cfg = cfg
        self.packet_contexts = []
        self.packet_context_by_idx = {}


class PacketContext(_RuntimeContext):
    def __init__(self, rm_ctx, packet_cfg):
        _RuntimeContext.__init__(self)
        self.rm_ctx = rm_ctx
        self.packet_cfg = packet_cfg
        self.cell_contexts = []
        self.cell_context_by_idx = {}

    def _packet_index(self):
        return self.packet_cfg.packet_index

    def _parent_context(self):
        return self.rm_ctx


class CellContext(_RuntimeContext):
    def __init__(self, rm_ctx, packet_ctx, cell_cfg):
        _RuntimeContext.__init__(self)
        self.rm_ctx = rm_ctx
        self.packet_ctx = packet_ctx
        self.cell_cfg = cell_cfg

    def _packet_index(self):
        return self.packet_ctx.packet_cfg.packet_index

    def _cell_index(self):
        return self.cell_cfg.cell_index

    def _parent_context(self):
        return self.packet_ctx
