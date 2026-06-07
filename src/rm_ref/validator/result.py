ERROR = "error"
WARNING = "warning"


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
