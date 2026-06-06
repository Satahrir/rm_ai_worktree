DEBUG = "debug"
TRACE = "trace"
WARNING = "warning"
ERROR = "error"


class Diagnostic(object):
    def __init__(
        self,
        severity,
        code,
        message,
        packet_index=None,
        cell_index=None,
        fields=None,
    ):
        self.severity = severity
        self.code = code
        self.message = message
        self.packet_index = packet_index
        self.cell_index = cell_index
        self.fields = dict(fields or {})

    def __repr__(self):
        return (
            "Diagnostic(severity={0!r}, code={1!r}, message={2!r}, "
            "packet_index={3!r}, cell_index={4!r}, fields={5!r})"
        ).format(
            self.severity,
            self.code,
            self.message,
            self.packet_index,
            self.cell_index,
            self.fields,
        )
