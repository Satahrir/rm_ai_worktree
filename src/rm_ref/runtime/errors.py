class RuntimeOrchestrationError(Exception):
    pass


class PayloadMappingError(RuntimeOrchestrationError):
    def __init__(
        self,
        message,
        packet_index=None,
        cell_index=None,
    ):
        RuntimeOrchestrationError.__init__(self, message)
        self.packet_index = packet_index
        self.cell_index = cell_index
