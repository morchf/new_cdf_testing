import abc
import base64
import logging
from typing import Callable, Dict, Generic, Set, Type, TypeVar

from pydantic import BaseModel, parse_raw_as
from redis.client import PubSubWorkerThread

from gtt.data_model.redis import PubSubMessage, RedisKey

from .redis import Redis

T = TypeVar("T")


class _RedisSubscriber(Generic[T], abc.ABC):
    """Utility class for subscribing to redis key/channel pairs"""

    _key: RedisKey
    redis: Redis
    _subscribers: Set[Callable[[PubSubMessage[T]], None]]
    _current_msg: PubSubMessage[T]
    _thread: PubSubWorkerThread

    def __init__(
        self,
        key: RedisKey,
        redis: Redis = None,
        daemon: bool = True,
    ) -> None:
        """Creates a new RedisSubscriber object that will constantly poll redis
        for new updates on the given RedisKey's channel. As many subscribers as
        necessary can subscribe to this single object and receive realtime updates
        as PUBLISH messages are sent to redis."""
        self._key = key
        self.redis = redis or Redis()
        self._subscribers = set()
        self._current_msg = None

        pubsub = self.redis.pubsub()
        logging.debug(f"Subscribing to: {self._key.channel()}")
        pubsub.psubscribe(**{self._key.channel(): self._message_handler})
        self._thread = pubsub.run_in_thread(sleep_time=60, daemon=daemon)

    def subscribe(self, subscriber: Callable[[PubSubMessage[T]], None]) -> None:
        """Adds a subscriber. The given callback function will be called whenever
        an update from redis is received."""
        self._subscribers.add(subscriber)

    def unsubscribe(self, subscriber: Callable[[PubSubMessage[T]], None]) -> None:
        """Removes a subscriber. The given callback function will no longer be called
        when new updates from redis are received."""
        self._subscribers.discard(subscriber)

    def get(self) -> PubSubMessage[T]:
        """Returns the last received update from redis"""
        return self._current_msg

    def stop(self) -> None:
        """Stops the redis PubSubWorkerThread that is constantly polling for updates
        from redis. New updates from redis will no longer be received or handled."""
        self._thread.stop()

    @property
    def key(self) -> RedisKey:
        return self.key.copy()

    def _message_handler(self, msg: Dict[str, bytes]):
        key = self._key.parse_key(msg["channel"].decode())
        raw_data = self.redis.get(key.key())
        pub_msg = msg["data"].decode()

        self._current_msg = PubSubMessage(
            key=key, data=self.deserialize(raw_data=raw_data), msg=pub_msg
        )

        for subscriber in self._subscribers:
            subscriber(self._current_msg)

    @abc.abstractmethod
    def deserialize(self, raw_data: str) -> T:
        pass


class RedisSubscriber(_RedisSubscriber[str]):
    def deserialize(self, raw_data: str) -> str:
        return raw_data


class BinaryRedisSubscriber(_RedisSubscriber[bytes]):
    def deserialize(self, raw_data: str) -> bytes:
        return base64.b64decode(raw_data)


ModelT = TypeVar("ModelT", bound=BaseModel)


class ModelRedisSubscriber(Generic[ModelT], _RedisSubscriber[ModelT]):
    model_type: Type[ModelT]

    def __init__(self, model_type: Type[ModelT], **kwargs) -> None:
        super().__init__(**kwargs)
        self.model_type = model_type

    def deserialize(self, raw_data: str) -> ModelT:
        return parse_raw_as(self.model_type, raw_data)
