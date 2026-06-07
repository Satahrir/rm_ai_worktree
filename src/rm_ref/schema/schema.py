class SchemaDefinition(object):
    def __init__(self, schema_id, word_width, word_count, fields, metadata=None):
        self.schema_id = schema_id
        self.word_width = word_width
        self.word_count = word_count
        self.fields = list(fields)
        self.metadata = dict(metadata or {})
        self._fields_by_name = dict(
            (field.normalized_name, field) for field in self.fields
        )
        self._aliases = {}
        for field in self.fields:
            self._add_alias(field.normalized_name, field)
            self._add_alias(field.name, field)
            self._add_alias(field.original_name, field)

    @classmethod
    def from_dict(cls, schema_dict):
        from rm_ref.schema.normalize import normalize_schema

        return normalize_schema(schema_dict)

    def _add_alias(self, name, field):
        if name is None:
            return
        from rm_ref.schema.normalize import normalize_field_name

        alias = normalize_field_name(name)
        existing = self._aliases.get(alias)
        if existing is None:
            self._aliases[alias] = field
        elif existing is not field:
            self._aliases[alias] = False

    def get_field(self, name):
        from rm_ref.schema.normalize import normalize_field_name

        normalized = normalize_field_name(name)
        field = self._aliases.get(normalized)
        if field is False:
            return None
        return field

    def require_field(self, name):
        from rm_ref.schema.errors import SchemaError

        field = self.get_field(name)
        if field is None:
            raise SchemaError(
                "schema {0} has no unambiguous field {1!r}".format(
                    self.schema_id, name
                )
            )
        return field

    def fields_for_scope(self, scope):
        return [field for field in self.fields if field.scope == scope]
