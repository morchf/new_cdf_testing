FROM_DIRECTION_ID_MAP = {1: "inbound", 0: "outbound"}

TO_DIRECTION_ID_MAP = dict(map(reversed, FROM_DIRECTION_ID_MAP.items()))


def from_direction(direction: str) -> str:
    return TO_DIRECTION_ID_MAP.get(direction)


def from_direction_id(direction: str) -> str:
    return FROM_DIRECTION_ID_MAP.get(direction)
