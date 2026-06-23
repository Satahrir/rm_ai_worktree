from rm_ref.core.diagnostic import to_plain_value


PASS = "PASS"
SETUP_ERROR = "SETUP_ERROR"
VALIDATION_ERROR = "VALIDATION_ERROR"
EXECUTION_ERROR = "EXECUTION_ERROR"


def _exception_to_dict(exception):
    if exception is None:
        return None
    result = {
        "type": exception.__class__.__name__,
        "message": str(exception),
    }
    for name in (
        "schema_id",
        "field_name",
        "value",
        "packet_index",
        "cell_index",
    ):
        if hasattr(exception, name):
            result[name] = to_plain_value(getattr(exception, name))
    return result


class OrchestrationResult(object):
    def __init__(
        self,
        status,
        validation=None,
        run_result=None,
        exception=None,
    ):
        if status not in (
            PASS,
            SETUP_ERROR,
            VALIDATION_ERROR,
            EXECUTION_ERROR,
        ):
            raise ValueError("invalid orchestration status {0!r}".format(status))
        self.status = status
        self.validation = validation
        self.run_result = run_result
        self.exception = exception

    def to_dict(self):
        validation = None
        if self.validation is not None:
            validation = self.validation.to_dict()
        run_result = None
        if self.run_result is not None:
            run_result = self.run_result.to_dict()
        return {
            "status": self.status,
            "validation": validation,
            "run_result": run_result,
            "exception": _exception_to_dict(self.exception),
        }
