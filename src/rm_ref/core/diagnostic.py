from copy import deepcopy


DEBUG = "debug"
TRACE = "trace"
WARNING = "warning"
ERROR = "error"


_SCALAR_TYPES = (type(None), bool, int, float, str)


def _sort_key(value):
    return (value.__class__.__name__, repr(value))


def to_plain_value(value):
    if isinstance(value, _SCALAR_TYPES):
        return value
    if isinstance(value, dict):
        result = {}
        for key in sorted(value, key=_sort_key):
            if not isinstance(key, _SCALAR_TYPES):
                raise TypeError(
                    "serialized dict keys must be scalar, got {0!r}".format(
                        key
                    )
                )
            result[deepcopy(key)] = to_plain_value(value[key])
        return result
    if isinstance(value, (list, tuple)):
        return [to_plain_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        plain_items = [to_plain_value(item) for item in value]
        return sorted(plain_items, key=_sort_key)
    raise TypeError(
        "serialized values must be dict, list, or scalar, got {0!r}".format(
            value
        )
    )


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

    def to_dict(self):
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "packet_index": self.packet_index,
            "cell_index": self.cell_index,
            "fields": to_plain_value(self.fields),
        }

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
