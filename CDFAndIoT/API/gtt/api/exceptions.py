class NotFoundException(Exception):
    """Raised when the item is not found"""

    pass


class ServerError(Exception):
    """Raised when an internal application issue causes a problem"""

    pass
