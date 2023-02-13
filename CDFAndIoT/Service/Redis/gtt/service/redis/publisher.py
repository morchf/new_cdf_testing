import abc
import base64
import logging
from typing import Generic, TypeVar

from pydantic import BaseModel

from gtt.data_model.redis import PubSubMessage

from .redis import Redis

T = TypeVar("T")


class _RedisPublisher(Generic[T], abc.ABC):
    """Utility class for publishing messages to Redis. Unlike a regular redis
    PUBLISH, the utility method in this class follows the convention of caching
    the relevant data rather than sending it in the publish message so that it's
    persisted.
    """

    redis: Redis

    def __init__(self, redis: Redis = None):
        """Creates a new RedisPublisher object for publishing to a redis key/channel pair"""
        self.redis = redis or Redis()

    def publish(self, message: PubSubMessage[T]):
        """Publishes the given data to redis with an optional message. The `data`
        parameter will be stored in the *key* associated with the given RedisKey.
        The `msg` parameter will be sent along with the PUBLISH message on the
        *channel* associated with the given RedisKey."""
        self.redis.set(message.key.key(), self.serialize(message.data))
        logging.debug(f"Publishing to {message.key.channel()}")
        self.redis.publish(message.key.channel(), message.msg)

    @abc.abstractmethod
    def serialize(self, data: T) -> str:
        pass


class RedisPublisher(_RedisPublisher[str]):
    def serialize(self, data: str) -> str:
        return data


class BinaryRedisPublisher(_RedisPublisher[bytes]):
    def serialize(self, data: bytes) -> str:
        return base64.b64encode(data).decode()


class ModelRedisPublisher(_RedisPublisher[BaseModel]):
    def serialize(self, data: BaseModel) -> str:
        return data.json()
