import redis
from json import loads
from os import environ
import threading
import json
import sys, os

threads = []


def connectToRedis():
    # These two parameters below needs to be set in the environment variable.
    redis_address = environ["RedisEndpointAddress"]  # redis_cache
    redis_port = environ["RedisEndpointPort"]
    # the parameter -> "utf-8" allows to convert to Unicode, since Redis returns binary Data.
    cache = redis.Redis(
        host=redis_address,
        port=redis_port,
        db=0,
        charset="utf-8",
        decode_responses=True,
    )  # redis_cache
    return cache


def processMessage(message, event):
    # print(f"message = {message}")
    data = loads(message["body"])
    print(f"data = {data}")
    # get SN from topic
    client_id = data.get("DeviceId")
    # print(f"client_id = {client_id}")
    cache = connectToRedis()
    # get data from the cache
    try:
        redis_cache_data = cache.hgetall(client_id.lower())  # redis_cache
        # Epoch time is used for the key

        placeholder = {
            "Ignition": True,
            "LeftTurn": False,
            "RightTurn": False,
            "Enabled": True,
            "DisabledMode": False,
        }
        if redis_cache_data:
            print(f"Preset Data = {redis_cache_data}")
            alteration = loads(data.get("msgData"))
            print(f'Initial GPIO = {redis_cache_data["GPIO"]}')
            jsoned = redis_cache_data.get("GPIO", json.dumps(placeholder))
            print(f"json conversion of cache data = {jsoned}")
            if jsoned != placeholder:
                jsoned = loads(jsoned)
            else:
                print("Placeholder active")
            print(f'Input = {alteration["Input"]}')
            print(f'Activation = {alteration["Activation"]}')
            jsoned[alteration["Input"]] = alteration["Activation"]
            print(f"updated jsoned = {jsoned}")
            redis_cache_data["GPIO"] = json.dumps(jsoned)
            if alteration["Input"] == "Ignition" and alteration["Activation"] == False:
                print("IGNITION DISABLED!!!")
                placeholder["Ignition"] = False
                redis_cache_data["GPIO"] = json.dumps(placeholder)

            cache.hmset(client_id, redis_cache_data)
            redis_cache_data = cache.hgetall(client_id.lower())
        else:
            print("NO CACHE")
            return

    except Exception as e:
        print(f"[ERROR] - {e}")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)


def lambda_handler(event, context):
    print(event)
    if not event.get("Records"):
        print("No Records")
        return

    for message in event["Records"]:
        thread = threading.Thread(target=processMessage, args=(message, event))
        thread.start()
        threads.append(thread)

    for x in threads:
        x.join()
