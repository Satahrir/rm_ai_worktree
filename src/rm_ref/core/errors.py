class CoreError(Exception):
    pass


class ConfigError(CoreError):
    pass


class DuplicateIndexError(ConfigError):
    pass
