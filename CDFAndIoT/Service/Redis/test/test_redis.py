from dataclasses import dataclass
from typing import Any, Callable, ClassVar, Dict, List

from gtt.service.redis import ModelCache, PubSubMessage, RedisPublisher, RedisSubscriber
from pydantic import BaseModel

from gtt.data_model.redis import WILDCARD, RedisKey


# Redis Mocking
@dataclass
class Call:
    args: List[Any]
    kwargs: Dict[str, Any]


class MockPubsubWorkerThread:
    running: bool

    def __init__(self) -> None:
        self.running = False

    def stop(self):
        self.running = False


class MockRedisPubsub:
    subscribers: Dict[str, Callable[[Dict[str, str]], None]]
    mock_thread: MockPubsubWorkerThread

    def __init__(self) -> None:
        self.subscribers = {}
        self.mock_thread = MockPubsubWorkerThread()

    def psubscribe(self, **kwargs):
        self.subscribers.update(kwargs)

    def run_in_thread(self, *args, **kwargs):
        self.mock_thread.running = True
        return self.mock_thread


class MockRedis:
    dummy_data: str

    sets: List[Dict[str, str]]
    publishes: List[Dict[str, str]]
    mock_pubsub: MockRedisPubsub

    def __init__(self) -> None:
        self.sets = []
        self.publishes = []
        self.mock_pubsub = MockRedisPubsub()

    def set(self, key, data):
        self.sets.append({"key": key, "data": data})

    def get(self, *args, **kwargs):
        return self.dummy_data

    def publish(self, channel, data):
        self.publishes.append({"channel": channel, "data": data})

    def pubsub(self):
        return self.mock_pubsub


class MockListener:
    msg: PubSubMessage

    def handle_message(self, msg: PubSubMessage):
        self.msg = msg


# Example Classes
class MyRedisKey(RedisKey):
    prefix: ClassVar[str] = "foo"

    a: str
    b: str
    c: str


class MyDataModel(BaseModel):
    foo: str
    bar: int
    baz: bool


def test_subscriber():
    # Create a channel subscribe filter on "foo:a:apple:b:banana:c:*"
    mock_redis = MockRedis()
    key = MyRedisKey(a="apple", b="banana", c=WILDCARD)

    # Initialize subscriber with auto-serialization for 'MyDataModel'
    subscriber: RedisSubscriber[MyDataModel] = RedisSubscriber(
        redis=mock_redis, key=key, cache_type=ModelCache(MyDataModel)
    )
    assert mock_redis.mock_pubsub.mock_thread.running
    assert len(mock_redis.mock_pubsub.subscribers) == 1
    assert key.channel() in mock_redis.mock_pubsub.subscribers.keys()

    # Add a listener to the redis subscriber
    mock_listener = MockListener()
    subscriber.subscribe(mock_listener.handle_message)

    # Simulate a publish message by directly calling the handler
    my_data = MyDataModel(foo="abcdefg", bar=5, baz=False)
    mock_redis.dummy_data = my_data.json()
    message_handler = mock_redis.mock_pubsub.subscribers[key.channel()]
    message_handler(
        {
            "channel": MyRedisKey(a="apple", b="banana", c="canteloupe")
            .channel()
            .encode(),
            "data": "foo".encode(),
        }
    )
    assert mock_listener.msg == PubSubMessage(
        key=MyRedisKey(a="apple", b="banana", c="canteloupe"),
        pub_message="foo",
        data=my_data,
    )

    # Remove listener from redis subscriber and ensure it doesn't receive updates
    subscriber.unsubscribe(mock_listener.handle_message)
    previous_mock_listener_msg = mock_listener.msg
    mock_redis.dummy_data = MyDataModel(foo="bad", bar=-1, baz=True).json()
    message_handler(
        {
            "channel": MyRedisKey(a="aardvark", b="bonobo", c="chinchila")
            .channel()
            .encode(),
            "data": "new update".encode(),
        }
    )
    assert mock_listener.msg == previous_mock_listener_msg

    # Ensure that the `stop()` method stops the pubsub worker thread
    subscriber.stop()
    assert not mock_redis.mock_pubsub.mock_thread.running


def test_redis_publisher():
    # Instantiate publisher with auto-serialization for 'MyDataModel'
    mock_redis = MockRedis()
    publisher: RedisPublisher[MyDataModel] = RedisPublisher(
        redis=mock_redis, cache_type=ModelCache(MyDataModel)
    )
    assert mock_redis.publishes == []

    # Try publishing invalid data
    publish_key = MyRedisKey(a="apple", b="banana", c="canteloupe")
    try:
        publisher.publish(PubSubMessage(key=publish_key, data="abcdefg"))
    except Exception as e:
        assert e is not None
    else:
        raise AssertionError(
            "Publishing 'abcdefg' should raise an exception with a model cache"
        )

    # Publish valid data
    my_data = MyDataModel(foo="abcdefg", bar=1, baz=True)
    publisher.publish(PubSubMessage(key=publish_key, data=my_data))
    assert mock_redis.publishes == [{"channel": publish_key.channel(), "data": ""}]
    assert mock_redis.sets == [{"key": publish_key.key(), "data": my_data.json()}]

    # Publish valid data with message
    publisher.publish(PubSubMessage(key=publish_key, data=my_data, msg="Hello, world!"))
    assert mock_redis.publishes[-1] == {
        "channel": publish_key.channel(),
        "data": "Hello, world!",
    }
    assert mock_redis.sets[-1] == {"key": publish_key.key(), "data": my_data.json()}
