class ConfigError(Exception):
    pass


class ConfigResolutionError(ConfigError):
    def __init__(
        self,
        message,
        schema_id=None,
        field_name=None,
        value=None,
        packet_index=None,
        cell_index=None,
    ):
        ConfigError.__init__(self, message)
        self.schema_id = schema_id
        self.field_name = field_name
        self.value = value
        self.packet_index = packet_index
        self.cell_index = cell_index
