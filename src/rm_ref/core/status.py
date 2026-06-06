OK = "OK"
WARNING = "WARNING"
ERROR = "ERROR"
SKIPPED = "SKIPPED"


_STATUS_RANK = {
    OK: 0,
    SKIPPED: 1,
    WARNING: 2,
    ERROR: 3,
}


def combine_status(current, incoming):
    if current not in _STATUS_RANK:
        raise ValueError("unknown current status: {0!r}".format(current))
    if incoming not in _STATUS_RANK:
        raise ValueError("unknown incoming status: {0!r}".format(incoming))
    if _STATUS_RANK[incoming] > _STATUS_RANK[current]:
        return incoming
    return current
