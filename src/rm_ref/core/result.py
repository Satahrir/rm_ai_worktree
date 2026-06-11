from copy import deepcopy

from rm_ref.core.diagnostic import to_plain_value


def _diagnostics_to_dict(diagnostics):
    return [diagnostic.to_dict() for diagnostic in diagnostics]


def _exception_to_dict(exception):
    if exception is None:
        return None
    return {
        "type": exception.__class__.__name__,
        "message": str(exception),
    }


class CellOutput(object):
    def __init__(
        self,
        packet_index,
        cell_index,
        status,
        warnings=None,
        errors=None,
        output=None,
    ):
        self.packet_index = packet_index
        self.cell_index = cell_index
        self.status = status
        self.warnings = list(warnings or [])
        self.errors = list(errors or [])
        self.output = deepcopy(output or {})

    def to_dict(self):
        return {
            "packet_index": self.packet_index,
            "cell_index": self.cell_index,
            "status": self.status,
            "warnings": _diagnostics_to_dict(self.warnings),
            "errors": _diagnostics_to_dict(self.errors),
            "output": to_plain_value(self.output),
        }


class PacketOutput(object):
    def __init__(
        self,
        packet_index,
        status,
        warnings=None,
        errors=None,
        runtime_summary=None,
        cell_outputs=None,
    ):
        self.packet_index = packet_index
        self.status = status
        self.warnings = list(warnings or [])
        self.errors = list(errors or [])
        self.runtime_summary = deepcopy(runtime_summary or {})
        self.cell_outputs = list(cell_outputs or [])

    def to_dict(self):
        return {
            "packet_index": self.packet_index,
            "status": self.status,
            "warnings": _diagnostics_to_dict(self.warnings),
            "errors": _diagnostics_to_dict(self.errors),
            "runtime_summary": to_plain_value(self.runtime_summary),
            "cell_outputs": [
                cell_output.to_dict()
                for cell_output in self.cell_outputs
            ],
        }


class RunResult(object):
    def __init__(
        self,
        status,
        exit_code,
        case_name,
        algorithm_name,
        summary=None,
        packet_outputs=None,
        warnings=None,
        errors=None,
        exception=None,
    ):
        self.status = status
        self.exit_code = exit_code
        self.case_name = case_name
        self.algorithm_name = algorithm_name
        self.summary = deepcopy(summary or {})
        self.packet_outputs = list(packet_outputs or [])
        self.warnings = list(warnings or [])
        self.errors = list(errors or [])
        self.exception = exception

    def to_dict(self):
        return {
            "status": self.status,
            "exit_code": self.exit_code,
            "case_name": self.case_name,
            "algorithm_name": self.algorithm_name,
            "summary": to_plain_value(self.summary),
            "packet_outputs": [
                packet_output.to_dict()
                for packet_output in self.packet_outputs
            ],
            "warnings": _diagnostics_to_dict(self.warnings),
            "errors": _diagnostics_to_dict(self.errors),
            "exception": _exception_to_dict(self.exception),
        }


def build_cell_output(cell_ctx):
    return CellOutput(
        packet_index=cell_ctx.packet_ctx.packet_cfg.packet_index,
        cell_index=cell_ctx.cell_cfg.cell_index,
        status=cell_ctx.status,
        warnings=cell_ctx.warnings,
        errors=cell_ctx.errors,
        output=cell_ctx.runtime["output"],
    )


def build_packet_output(packet_ctx):
    runtime_summary = {
        "active_cell_count": packet_ctx.get_derived("active_cell_count", 0),
        "executed_cell_count": len(packet_ctx.cell_contexts),
    }
    return PacketOutput(
        packet_index=packet_ctx.packet_cfg.packet_index,
        status=packet_ctx.status,
        warnings=packet_ctx.warnings,
        errors=packet_ctx.errors,
        runtime_summary=runtime_summary,
        cell_outputs=[
            build_cell_output(cell_ctx)
            for cell_ctx in packet_ctx.cell_contexts
        ],
    )


def build_run_result(rm_ctx, algorithm_name, exception=None):
    cell_count = sum(
        len(packet_ctx.cell_contexts)
        for packet_ctx in rm_ctx.packet_contexts
    )
    summary = {
        "packet_count": len(rm_ctx.packet_contexts),
        "cell_count": cell_count,
        "warning_count": len(rm_ctx.warnings),
        "error_count": len(rm_ctx.errors),
    }
    return RunResult(
        status=rm_ctx.status,
        exit_code=0 if not rm_ctx.errors and exception is None else 1,
        case_name=rm_ctx.cfg.case_name,
        algorithm_name=algorithm_name,
        summary=summary,
        packet_outputs=[
            build_packet_output(packet_ctx)
            for packet_ctx in rm_ctx.packet_contexts
        ],
        warnings=rm_ctx.warnings,
        errors=rm_ctx.errors,
        exception=exception,
    )
