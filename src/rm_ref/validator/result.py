from copy import deepcopy


ERROR = "error"
WARNING = "warning"


_SCALAR_TYPES = (type(None), bool, int, float, str)


def _sort_key(value):
    return (value.__class__.__name__, repr(value))


def _to_plain_value(value):
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
            result[deepcopy(key)] = _to_plain_value(value[key])
        return result
    if isinstance(value, (list, tuple)):
        return [_to_plain_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        plain_items = [_to_plain_value(item) for item in value]
        return sorted(plain_items, key=_sort_key)
    raise TypeError(
        "serialized values must be dict, list, or scalar, got {0!r}".format(
            value
        )
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
