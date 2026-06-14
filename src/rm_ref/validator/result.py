from copy import deepcopy
import struct


ERROR = "error"
WARNING = "warning"


_SCALAR_TYPES = (type(None), bool, int, float, str)


def _is_scalar(value):
    return type(value) in _SCALAR_TYPES


def _plain_sort_key(value):
    value_type = type(value)
    if value is None:
        return (0,)
    if value_type is bool:
        return (1, int(value))
    if value_type is int:
        return (2, value)
    if value_type is float:
        return (3, struct.pack(">d", value))
    if value_type is str:
        return (4, value)
    if value_type is list:
        return (5, tuple(_plain_sort_key(item) for item in value))
    if value_type is dict:
        return (
            6,
            tuple(
                (
                    _plain_sort_key(key),
                    _plain_sort_key(value[key]),
                )
                for key in sorted(value, key=_plain_sort_key)
            ),
        )
    raise TypeError("serialized values must be dict, list, or scalar")


def _to_plain_value(value):
    if _is_scalar(value):
        return value
    value_type = type(value)
    if value_type is dict:
        for key in value:
            if not _is_scalar(key):
                raise TypeError(
                    "serialized dict keys must be scalar"
                )
        result = {}
        for key in sorted(value, key=_plain_sort_key):
            result[deepcopy(key)] = _to_plain_value(value[key])
        return result
    if value_type in (list, tuple):
        return [_to_plain_value(item) for item in value]
    if value_type in (set, frozenset):
        plain_items = [_to_plain_value(item) for item in value]
        return sorted(plain_items, key=_plain_sort_key)
    raise TypeError(
        "serialized values must be dict, list, or scalar"
    )


class ValidationIssue(object):
    def __init__(
        self,
        code,
        message,
        severity=ERROR,
        schema_id=None,
        field_name=None,
        original_field_name=None,
        packet_index=None,
        cell_index=None,
        value=None,
        expected_rule=None,
        word=None,
        msb=None,
        lsb=None,
        width=None,
        description="",
        rule_name=None,
    ):
        if severity not in (ERROR, WARNING):
            raise ValueError("invalid validation severity {0!r}".format(severity))
        self.code = code
        self.message = message
        self.severity = severity
        self.schema_id = schema_id
        self.field_name = field_name
        self.original_field_name = original_field_name
        self.packet_index = packet_index
        self.cell_index = cell_index
        self.value = value
        self.expected_rule = expected_rule
        self.word = word
        self.msb = msb
        self.lsb = lsb
        self.width = width
        self.description = description or ""
        self.rule_name = rule_name

    def to_dict(self):
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "schema_id": self.schema_id,
            "field_name": self.field_name,
            "original_field_name": self.original_field_name,
            "packet_index": self.packet_index,
            "cell_index": self.cell_index,
            "value": _to_plain_value(self.value),
            "expected_rule": self.expected_rule,
            "word": self.word,
            "msb": self.msb,
            "lsb": self.lsb,
            "width": self.width,
            "description": self.description,
            "rule_name": self.rule_name,
        }

    def __repr__(self):
        return (
            "ValidationIssue(code={0!r}, severity={1!r}, field_name={2!r}, "
            "packet_index={3!r}, cell_index={4!r}, value={5!r})"
        ).format(
            self.code,
            self.severity,
            self.field_name,
            self.packet_index,
            self.cell_index,
            self.value,
        )


class ValidationResult(object):
    def __init__(self):
        self.errors = []
        self.warnings = []

    @property
    def ok(self):
        return not self.errors

    def add(self, issue):
        if not isinstance(issue, ValidationIssue):
            raise TypeError("issue must be ValidationIssue")
        if issue.severity == ERROR:
            self.errors.append(issue)
        else:
            self.warnings.append(issue)
        return issue

    def add_error(self, issue):
        if issue.severity != ERROR:
            raise ValueError("error issue must have error severity")
        return self.add(issue)

    def add_warning(self, issue):
        if issue.severity != WARNING:
            raise ValueError("warning issue must have warning severity")
        return self.add(issue)

    def to_dict(self):
        return {
            "ok": self.ok,
            "errors": [issue.to_dict() for issue in self.errors],
            "warnings": [issue.to_dict() for issue in self.warnings],
        }
