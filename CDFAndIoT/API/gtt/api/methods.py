from typing import Literal, Union

HttpMethod = Union[
    Literal["DELETE"],
    Literal["HEAD"],
    Literal["OPTIONS"],
    Literal["PATCH"],
    Literal["POST"],
    Literal["PUT"],
    Literal["GET"],
]
