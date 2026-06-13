class CoreError(Exception):
    pass


class FrameworkError(CoreError):
    pass


class AlgorithmContextUsageError(CoreError):
    pass


class AlgorithmExecutionError(CoreError):
    def __init__(
        self,
        message,
        original_exception=None,
        packet_index=None,
        cell_index=None,
        algorithm_name=None,
    ):
        CoreError.__init__(self, message)
        self.original_exception = original_exception
        self.packet_index = packet_index
        self.cell_index = cell_index
        self.algorithm_name = algorithm_name


class DiagnosticRecordingError(FrameworkError):
    def __init__(self, message, primary_error=None, recording_error=None):
        FrameworkError.__init__(self, message)
        self.primary_error = primary_error
        self.recording_error = recording_error


class LifecycleFinalizationError(FrameworkError):
    def __init__(self, message, primary_error=None, finalizer_errors=None):
        FrameworkError.__init__(self, message)
        self.primary_error = primary_error
        self.finalizer_errors = list(finalizer_errors or [])


class ConfigError(CoreError):
    """Invalid caller-supplied core configuration or API contract."""

    pass


class DuplicateIndexError(ConfigError):
    pass
