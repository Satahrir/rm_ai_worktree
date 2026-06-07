class SchemaError(Exception):
    pass


class DuplicateSchemaError(SchemaError):
    pass


class SchemaNotFoundError(SchemaError):
    pass
