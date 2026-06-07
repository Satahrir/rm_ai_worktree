from copy import deepcopy


_MISSING = object()


class FieldDefinition(object):
    def __init__(
        self,
        name,
        normalized_name,
        original_name,
        word=None,
        msb=None,
        lsb=None,
        width=None,
        enum=None,
        default=_MISSING,
        minimum=None,
        maximum=None,
        description="",
        instance=None,
        group=None,
        reserved=False,
        required=False,
        scope="cell",
    ):
        self.name = name
        self.normalized_name = normalized_name
        self.original_name = original_name
        self.word = word
        self.msb = msb
        self.lsb = lsb
        self.width = width
        self.enum = deepcopy(enum or {})
        if default is _MISSING:
            self.default = _MISSING
        else:
            self.default = deepcopy(default)
        self.min = minimum
        self.max = maximum
        self.description = description or ""
        self.instance = instance
        self.group = group
        self.reserved = bool(reserved)
        self.required = bool(required) and not self.reserved
        self.scope = scope

    @property
    def has_default(self):
        return self.default is not _MISSING

    @property
    def bit_range(self):
        if self.msb is None or self.lsb is None:
            return None
        return (self.msb, self.lsb)

    def enum_values(self):
        return list(self.enum.values())

    def __repr__(self):
        return (
            "FieldDefinition(name={0!r}, normalized_name={1!r}, "
            "original_name={2!r}, scope={3!r})"
        ).format(
            self.name,
            self.normalized_name,
            self.original_name,
            self.scope,
        )
