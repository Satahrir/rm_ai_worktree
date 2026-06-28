from rm_ref.config import UserConfig
from rm_ref.io.uvm_table.config_adapter import (
    UvmTableConfigAdapterError,
    bind_config_from_uvm_table_json,
)
from rm_ref.io.uvm_table.parser import UvmTableParserError, parse_uvm_table_tree
from rm_ref.runtime.runner import run_case


PARSE_ERROR = "PARSE_ERROR"
BINDING_ERROR = "BINDING_ERROR"
CONFIG_ERROR = "CONFIG_ERROR"
RUNTIME_COMPLETED = "RUNTIME_COMPLETED"


class UvmTableCaseResult(object):
    def __init__(
        self,
        status,
        parse_report=None,
        parse_error=None,
        binding_report=None,
        binding_error=None,
        user_config_dict=None,
        orchestration_result=None,
        errors=None,
        warnings=None,
    ):
        if status not in (
            PARSE_ERROR,
            BINDING_ERROR,
            CONFIG_ERROR,
            RUNTIME_COMPLETED,
        ):
            raise ValueError("invalid UVM table case status {0!r}".format(status))
        self.status = status
        self.parse_report = parse_report
        self.parse_error = parse_error
        self.binding_report = binding_report
        self.binding_error = binding_error
        self.user_config_dict = user_config_dict
        self.orchestration_result = orchestration_result
        self.errors = list(errors or [])
        self.warnings = list(warnings or [])

    def to_dict(self):
        orchestration_result = None
        if self.orchestration_result is not None:
            orchestration_result = self.orchestration_result.to_dict()
        return {
            "status": self.status,
            "parse_report": self.parse_report,
            "parse_error": _exception_to_dict(self.parse_error),
            "binding_report": self.binding_report,
            "binding_error": _exception_to_dict(self.binding_error),
            "user_config_dict": self.user_config_dict,
            "orchestration_result": orchestration_result,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def _exception_to_dict(exception):
    if exception is None:
        return None
    return {
        "type": exception.__class__.__name__,
        "message": str(exception),
    }


def _parse_report(roots):
    return {
        "root_count": len(roots),
        "root_names": [root.get("name") for root in roots],
    }


def _format_binding_errors(report):
    messages = []
    for item in report.get("errors") or []:
        message = item.get("message")
        if message is not None:
            messages.append(message)
    return messages


def run_uvm_table_text_case(
    text,
    schema,
    algorithm,
    payload_by_packet=None,
    scope_rules=None,
    default_packet_index=0,
    default_cell_index=0,
):
    try:
        roots = parse_uvm_table_tree(text)
    except UvmTableParserError as exc:
        return UvmTableCaseResult(
            status=PARSE_ERROR,
            parse_error=exc,
            errors=[str(exc)],
        )

    return run_uvm_table_json_case(
        {"format": "uvm_table_printer/v1", "roots": roots},
        schema,
        algorithm,
        payload_by_packet=payload_by_packet,
        scope_rules=scope_rules,
        default_packet_index=default_packet_index,
        default_cell_index=default_cell_index,
        parse_report=_parse_report(roots),
    )


def run_uvm_table_json_case(
    uvm_table_json,
    schema,
    algorithm,
    payload_by_packet=None,
    scope_rules=None,
    default_packet_index=0,
    default_cell_index=0,
    parse_report=None,
):
    try:
        binding = bind_config_from_uvm_table_json(
            uvm_table_json,
            schema,
            scope_rules=scope_rules,
            default_packet_index=default_packet_index,
            default_cell_index=default_cell_index,
        )
    except UvmTableConfigAdapterError as exc:
        return UvmTableCaseResult(
            status=BINDING_ERROR,
            parse_report=parse_report,
            binding_error=exc,
            errors=[str(exc)],
        )

    if binding.has_errors:
        return UvmTableCaseResult(
            status=BINDING_ERROR,
            parse_report=parse_report,
            binding_report=binding.report,
            errors=_format_binding_errors(binding.report),
            warnings=list(binding.report.get("warnings") or []),
        )

    try:
        user_config = UserConfig.from_dict(binding.config_dict)
    except Exception as exc:
        return UvmTableCaseResult(
            status=CONFIG_ERROR,
            parse_report=parse_report,
            binding_report=binding.report,
            user_config_dict=binding.config_dict,
            errors=[str(exc)],
        )

    orchestration_result = run_case(
        user_config,
        schema,
        algorithm,
        payload_by_packet=payload_by_packet,
    )
    return UvmTableCaseResult(
        status=RUNTIME_COMPLETED,
        parse_report=parse_report,
        binding_report=binding.report,
        user_config_dict=binding.config_dict,
        orchestration_result=orchestration_result,
        warnings=list(binding.report.get("warnings") or []),
    )
