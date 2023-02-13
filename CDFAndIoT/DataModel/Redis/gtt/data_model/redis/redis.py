from typing import ClassVar, Generic, Type, TypeVar

from pydantic import BaseModel

WILDCARD = "*"

Self = TypeVar("Self", bound="RedisKey")


class RedisKey(BaseModel):
    """
    Base Class for creating 'Redis Key' pydantic models. Field names and values
    will correspond to the respective parts of the redis key and channel strings
    that are built with the `key()` and `channel()` methods.

    Example child class:

    ```python
        class VehiclePositionsKey(RedisKey):
            prefix: ClassVar[str] = "tsp_in_cloud:vehicle_positions"

            agency: str
            trip: str
            vehicle: str
    ```

    Example key
    ```python
        VehiclePositionsKey(agency="tsptest", trip=WILDCARD, vehicle="vehicle-001").key()
    ```
    Output:
    ```text
        tsp_in_cloud:vehicle_positions:agency:tsptest:trip:*:vehicle:vehicle-001
    ```

    Example channel
    ```python
        VehiclePositionsKey(agency="tsptest", trip=WILDCARD, vehicle=WILDCARD).channel()
    ```
    Output:
    ```text
        tsp_in_cloud:vehicle_positions_new:agency:tsptest:trip:*:vehicle:*
    ```
    Notice the `_new` suffix after `tsp_in_cloud:vehicle_positions`
    """

    prefix: ClassVar[str]

    def key(self):
        return self.__class__.prefix + self._key_body()

    def channel(self):
        return f"{self.__class__.prefix}_new" + self._key_body()

    def _key_body(self):
        return "".join([f":{name}:{value}" for name, value in self.dict().items()])

    @classmethod
    def parse_key(cls: Type[Self], channel: str) -> Self:
        num_parts = len(cls.__fields__) * 2
        channel_parts = channel.split(":")
        field_parts = channel_parts[-num_parts:]
        key_args = {field_parts[i]: field_parts[i + 1] for i in range(0, num_parts, 2)}
        return cls(**key_args)


T = TypeVar("T")


class PubSubMessage(BaseModel, Generic[T]):
    """
    `key`:      The RedisKey associated with this publish message,
                    derived from the channel it was sent on.
    `data`:     The data in the cache associated with the channel this message
                    was sent on.
    `msg`:      The PUBLISH message's 'data'
    """

    key: RedisKey
    data: T
    msg: str = ""
