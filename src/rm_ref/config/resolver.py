from copy import deepcopy

from rm_ref.config.errors import ConfigResolutionError
from rm_ref.config.resolved_config import (
    ResolvedCellConfig,
    ResolvedConfig,
    ResolvedPacketConfig,
)
from rm_ref.config.user_config import UserConfig
from rm_ref.schema import (
    SchemaDefinition,
    SchemaNotFoundError,
    SchemaRegistry,
)


USER_SOURCE = "user"
SCHEMA_DEFAULT_SOURCE = "schema_default"


class ConfigResolver(object):
    def __init__(self, registry=None):
        if registry is not None and not isinstance(registry, SchemaRegistry):
            raise TypeError("registry must be SchemaRegistry or None")
        self.registry = registry

    def _get_schema(self, user_config, schema):
        if schema is not None:
            if not isinstance(schema, SchemaDefinition):
                raise TypeError("schema must be SchemaDefinition or None")
            if (
                user_config.schema_id is not None
                and user_config.schema_id != schema.schema_id
            ):
                raise ConfigResolutionError(
                    "user config schema_id {0!r} does not match schema {1!r}".format(
                        user_config.schema_id, schema.schema_id
                    ),
                    schema_id=user_config.schema_id,
                )
            return schema
        if self.registry is None:
            raise ConfigResolutionError(
                "cannot resolve schema {0!r} without a registry".format(
                    user_config.schema_id
                ),
                schema_id=user_config.schema_id,
            )
        try:
            return self.registry.get(user_config.schema_id)
        except SchemaNotFoundError:
            raise ConfigResolutionError(
                "schema {0!r} is not registered".format(user_config.schema_id),
                schema_id=user_config.schema_id,
            )

    def _error(
        self,
        message,
        schema,
        field_name=None,
        value=None,
        packet_index=None,
        cell_index=None,
    ):
        raise ConfigResolutionError(
            message,
            schema_id=schema.schema_id,
            field_name=field_name,
            value=value,
            packet_index=packet_index,
            cell_index=cell_index,
        )

    def _convert_value(
        self,
        field,
        value,
        schema,
        packet_index=None,
        cell_index=None,
    ):
        if field.enum and isinstance(value, str):
            if value not in field.enum:
                self._error(
                    "schema {0} field {1} value {2!r} is not a known enum name; "
                    "expected one of {3}".format(
                        schema.schema_id,
                        field.normalized_name,
                        value,
                        sorted(field.enum.keys()),
                    ),
                    schema,
                    field_name=field.normalized_name,
                    value=value,
                    packet_index=packet_index,
                    cell_index=cell_index,
                )
            return field.enum[value]
        return deepcopy(value)

    def _resolve_values(
        self,
        raw_values,
        scope,
        schema,
        packet_index=None,
        cell_index=None,
    ):
        resolved = {}
        sources = {}
        for raw_name, raw_value in raw_values.items():
            field = schema.get_field(raw_name)
            if field is None:
                self._error(
                    "schema {0} has no unambiguous field {1!r}".format(
                        schema.schema_id, raw_name
                    ),
                    schema,
                    field_name=raw_name,
                    value=raw_value,
                    packet_index=packet_index,
                    cell_index=cell_index,
                )
            if field.scope != scope:
                self._error(
                    "schema {0} field {1} belongs to {2} scope, not {3} scope".format(
                        schema.schema_id,
                        field.normalized_name,
                        field.scope,
                        scope,
                    ),
                    schema,
                    field_name=field.normalized_name,
                    value=raw_value,
                    packet_index=packet_index,
                    cell_index=cell_index,
                )
            canonical_name = field.normalized_name
            if canonical_name in resolved:
                self._error(
                    "schema {0} field {1} was provided more than once through aliases".format(
                        schema.schema_id, canonical_name
                    ),
                    schema,
                    field_name=canonical_name,
                    value=raw_value,
                    packet_index=packet_index,
                    cell_index=cell_index,
                )
            resolved[canonical_name] = self._convert_value(
                field,
                raw_value,
                schema,
                packet_index=packet_index,
                cell_index=cell_index,
            )
            sources[canonical_name] = USER_SOURCE

        for field in schema.fields_for_scope(scope):
            if field.normalized_name not in resolved and field.has_default:
                resolved[field.normalized_name] = self._convert_value(
                    field,
                    field.default,
                    schema,
                    packet_index=packet_index,
                    cell_index=cell_index,
                )
                sources[field.normalized_name] = SCHEMA_DEFAULT_SOURCE
        return resolved, sources

    def resolve(self, user_config, schema=None):
        if not isinstance(user_config, UserConfig):
            raise TypeError("user_config must be UserConfig")
        schema = self._get_schema(user_config, schema)

        global_values, global_sources = self._resolve_values(
            user_config.global_values,
            "global",
            schema,
        )

        packets = []
        seen_packets = set()
        for packet_position, user_packet in enumerate(user_config.packets):
            packet_index = user_packet.packet_index
            if packet_index is None:
                packet_index = packet_position
            if packet_index in seen_packets:
                self._error(
                    "schema {0} has duplicate packet index {1!r}".format(
                        schema.schema_id, packet_index
                    ),
                    schema,
                    packet_index=packet_index,
                )
            seen_packets.add(packet_index)
            packet_values, packet_sources = self._resolve_values(
                user_packet.values,
                "packet",
                schema,
                packet_index=packet_index,
            )

            cells = []
            seen_cells = set()
            for cell_position, user_cell in enumerate(user_packet.cells):
                cell_index = user_cell.cell_index
                if cell_index is None:
                    cell_index = cell_position
                if cell_index in seen_cells:
                    self._error(
                        "schema {0} packet {1} has duplicate cell index {2!r}".format(
                            schema.schema_id, packet_index, cell_index
                        ),
                        schema,
                        packet_index=packet_index,
                        cell_index=cell_index,
                    )
                seen_cells.add(cell_index)
                cell_values, cell_sources = self._resolve_values(
                    user_cell.values,
                    "cell",
                    schema,
                    packet_index=packet_index,
                    cell_index=cell_index,
                )
                cells.append(
                    ResolvedCellConfig(
                        cell_index=cell_index,
                        values=cell_values,
                        value_sources=cell_sources,
                    )
                )

            packets.append(
                ResolvedPacketConfig(
                    packet_index=packet_index,
                    values=packet_values,
                    value_sources=packet_sources,
                    cells=cells,
                )
            )

        return ResolvedConfig(
            case_name=user_config.case_name,
            algorithm_name=user_config.algorithm_name,
            schema_id=schema.schema_id,
            global_values=global_values,
            global_value_sources=global_sources,
            packets=packets,
        )
