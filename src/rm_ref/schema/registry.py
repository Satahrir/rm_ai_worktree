from rm_ref.schema.errors import (
    DuplicateSchemaError,
    SchemaError,
    SchemaNotFoundError,
)
from rm_ref.schema.normalize import normalize_schema
from rm_ref.schema.schema import SchemaDefinition


class SchemaRegistry(object):
    def __init__(self):
        self._schemas = {}

    def register(self, schema):
        if isinstance(schema, dict):
            schema = normalize_schema(schema)
        if not isinstance(schema, SchemaDefinition):
            raise SchemaError(
                "schema must be SchemaDefinition or dict, got {0!r}".format(schema)
            )
        if schema.schema_id in self._schemas:
            raise DuplicateSchemaError(
                "schema {0} is already registered".format(schema.schema_id)
            )
        self._schemas[schema.schema_id] = schema
        return schema

    def get(self, schema_id):
        try:
            return self._schemas[schema_id]
        except KeyError:
            raise SchemaNotFoundError(
                "schema {0!r} is not registered".format(schema_id)
            )

    def has(self, schema_id):
        return schema_id in self._schemas

    def schema_ids(self):
        return sorted(self._schemas.keys())
