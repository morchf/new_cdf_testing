import base64
import json
import logging
import math
import os
import struct
import timeit

import boto3
import redis
import urllib3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session

# Create client here so that it will stay 'warm' between invocations
# saving us execution time
client = boto3.client("iot-data", os.environ["AWS_REGION"])
base_url = os.environ["CDF_URL"]
REDIS_URL = os.environ["REDIS_URL"]
REDIS_PORT = os.environ["REDIS_PORT"]


http = urllib3.PoolManager()
headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}

# Create the connection to the Redis Elasticache cluster
cache = redis.Redis(host=REDIS_URL, port=REDIS_PORT, db=0, decode_responses=True)

# Log Levels listed with the top level being the most verbose
# and the bottom being the least verbose:
# DEBUG
# INFO
# WARN
# ERROR
# FATAL
logging.basicConfig(level=logging.INFO)


def send_request(url, method, region_name, params=None, headers=None):
    # fmt: off
    request = AWSRequest(method=method.upper(), url=url, data=params, headers=headers,)
    logging.info(f"Created AWS Request: {request}. Region Name, URL, headers, params : {region_name, url, headers, params}")
    # fmt: on
    SigV4Auth(boto3.Session().get_credentials(), "execute-api", region_name).add_auth(
        request
    )
    logging.debug("SignV4Auth obtained. Trying to get data from CDF.")
    return URLLib3Session().send(request.prepare()).content


def lambda_handler(event, context):

    timeLambdaStart = timeit.default_timer()
    pub_topic = event.get("topic")
    logging.info(f"Message from topic: {pub_topic}")
    if not pub_topic:
        logging.error("No topic in event data")
        raise Exception("No topic in event data")
    message = event.get("data")
    logging.debug(f"Message before decode: {message} ")
    # Decode message back to bytes
    message = base64.standard_b64decode(message)
    logging.debug(f"Message after decode: {message} ")

    # Pull out client_id which is 2101EE0006 in Topic below
    # Example Topic: GTT/GTT/VEH/EVP/2101/2101EE0006/RTRADIO
    split_topic = pub_topic.split("/")

    # Update EVP to TSP to support later changes
    pub_topic = pub_topic.replace("TSP", "EVP")
    client_id = split_topic[5]
    logging.debug(f"Client ID: {client_id}")
    redis_key = f"cdf_cache:{client_id}"

    # get data from the cache
    try:
        timeToRedisConn = timeit.default_timer() - timeLambdaStart
        logging.debug(f"Trying redis connection. Time taken = {timeToRedisConn}")
        if cache:
            logging.debug("Cache connection success.")
        cache_data = cache.hgetall(name=redis_key)
        if cache_data:
            logging.debug(
                f"Cache Data fetched: {cache_data.get('ID')}. Time taken for fetch: {timeit.default_timer()-timeToRedisConn} ms"
            )
        else:
            logging.debug("Data not found in cache. Now checking CDF for the data.")

    except Exception as RedisFetchException:
        logging.error(f"Redis Fetch Exception: {RedisFetchException}")

    if cache_data.get("ID"):
        create_topic_and_publish(
            message,
            pub_topic,
            cache_data["vehicleID"],
            cache_data["vehicleClass"],
            cache_data["vehicleCityID"],
            cache_data["agencyID"],
            cache_data["ID"],
            cache_data["CMSID"],
        )
    else:
        # Assemble URL
        url = f"{base_url}/devices/{client_id.lower()}"

        logging.debug(f"CDF URL being hit : {url}")
        # get data
        code = send_request(url, "GET", os.environ["AWS_REGION"], headers=headers)

        logging.debug(f"Data from CDF: {code}")
        # Only work with good data
        if code:
            communicator_cdf_data = json.loads(code)

            logging.debug(f"Communicator CDF Data: {communicator_cdf_data}")
            template_id = communicator_cdf_data.get("templateId")

            if not template_id:
                logging.error(
                    f"Serial No. is {client_id} No template Id in device CDF data "
                )
                raise Exception(
                    f"Serial No. is {client_id} No template Id in device CDF data "
                )

            if template_id == "communicator":
                # get region and agency name from device CDF data
                groups = communicator_cdf_data.get("groups")
                if groups:
                    out = groups.get("out")
                else:
                    logging.error(f"Serial No. is {client_id} No groups in CDF data ")
                    raise Exception(f"Serial No. is {client_id} No groups in CDF data ")

                if out:
                    owned_by = out.get("ownedby")
                else:
                    owned_by = groups.get("ownedby")

                if owned_by:
                    agency = owned_by[0].split("/")[2]
                    region = owned_by[0].split("/")[1]
                else:
                    logging.error(
                        f"Serial No. is {client_id} No groups/ownedby in CDF data "
                    )
                    raise Exception(
                        f"Serial No. is {client_id} No groups/ownedby in CDF data "
                    )

                # use communicator data to get vehicle data
                devices = communicator_cdf_data.get("devices")

                if devices:
                    devices_in = devices.get("in")
                if not devices:
                    logging.error(
                        f"Serial No. is {client_id} No associated vehicle in"
                        " communicator CDF data "
                    )
                    raise Exception(
                        f"Serial No. is {client_id} No associated vehicle in"
                        " communicator CDF data "
                    )

                # sometimes device data has out sometimes it doesn't; handle both cases
                if devices_in:
                    owned_by = devices_in.get("installedat")
                else:
                    owned_by = devices.get("installedat")

                vehicle = owned_by[0]

                # Assemble URL for vehicle
                url = f"{base_url}/devices/{vehicle.lower()}"

                vehicle_cdf_data = send_request(
                    url, "GET", os.environ["AWS_REGION"], headers=headers
                )

                if not vehicle_cdf_data:
                    logging.error(
                        f"Serial No. is {client_id} Cannot get Vehicle data from CDF "
                    )
                    raise Exception(
                        f"Serial No. is {client_id} Cannot get Vehicle data from CDF "
                    )

                vehicle_cdf_data = json.loads(vehicle_cdf_data)
                vehicle_attributes = vehicle_cdf_data.get("attributes")

                if not vehicle_attributes:
                    logging.error(
                        f"Serial No. is {client_id} No attributes value in vehicle"
                        + " CDF data "
                    )
                    raise Exception(
                        f"Serial No. is {client_id} No attributes value in vehicle"
                        + " CDF data "
                    )

                if vehicle_attributes:
                    vehicle_id = vehicle_attributes.get("VID")
                    vehicle_class = vehicle_attributes.get("class")
                else:
                    logging.error(
                        f"Serial No. is {client_id} Cannot get VID/class from CDF "
                    )
                    raise Exception(
                        f"Serial No. is {client_id} Cannot get VID/class from CDF "
                    )

                # use communicator data to get agency data
                url = f"{base_url}/groups/%2F{region}%2F{agency}"

                agency_data = send_request(
                    url, "GET", os.environ["AWS_REGION"], headers=headers
                )

                if not agency_data:
                    logging.error(
                        f"Serial No. is {client_id} Cannot get Agency data from CDF "
                    )
                    raise Exception(
                        f"Serial No. is {client_id} Cannot get Agency data from CDF "
                    )

                agency_data = json.loads(agency_data)
                agency_attributes = agency_data.get("attributes")
                if not agency_attributes:
                    logging.error(
                        f"Serial No. is {client_id} attributes not found in CDF Agency "
                    )
                    raise Exception(
                        f"Serial No. is {client_id} attributes not found in CDF Agency "
                    )

                vehicle_city_id = agency_attributes.get("agencyCode")
                if not vehicle_city_id:
                    raise Exception(
                        f"Serial No. is {client_id} Agency Code not found in "
                        + "CDF Agency "
                    )

                agency_id = agency_attributes.get("agencyID")
                cms_id = agency_attributes.get("CMSId")
                if not cms_id:
                    raise Exception(
                        f"Serial No. is {client_id} CMS ID (GUID) not found in "
                        + "CDF Agency "
                    )
                if not agency_id:
                    raise Exception(
                        f"Serial No. is {client_id} Agency ID (GUID) not found in "
                        + "CDF Agency "
                    )

                create_topic_and_publish(
                    message,
                    pub_topic,
                    vehicle_id,
                    vehicle_class,
                    vehicle_city_id,
                    agency_id,
                    client_id,
                    cms_id,
                )
                insert_in_cache(
                    vehicle_id,
                    vehicle_class,
                    vehicle_city_id,
                    agency_id,
                    client_id.lower(),
                    cms_id,
                )
                logging.debug(
                    f" Total time taken for lambda execution: {timeit.default_timer()- timeLambdaStart} ms"
                )
            else:
                logging.error(
                    f"Serial No. is {client_id} template_id != communicator; exiting "
                )
                raise Exception(
                    f"Serial No. is {client_id} template_id != communicator; exiting "
                )
        else:
            logging.debug(f"Serial No. is {client_id} Cannot get Device data from CDF")
            raise Exception(
                f"Serial No. is {client_id} Cannot get Device data from CDF"
            )


def create_topic_and_publish(
    message,
    pub_topic,
    vehicle_id,
    vehicle_class,
    vehicle_city_id,
    agency_id,
    client_id,
    cms_id,
):
    vehicle_city_id = int(vehicle_city_id).to_bytes(1, byteorder="little", signed=False)
    vehicle_class = int(vehicle_class).to_bytes(1, byteorder="little", signed=False)
    vehicle_id = int(vehicle_id).to_bytes(2, byteorder="little", signed=False)
    # values of vehicle_id and vehicle_class are replaced with values
    # from CDF repository

    latitude = message[8:12]
    _latitude = struct.unpack("<i", latitude)[0]

    MINLATITUDE = -90
    MAXLATITUDE = 90

    _dec = _latitude * 0.000001
    _dec_int = math.trunc(_dec)
    # Minutes shift over two decimal places and divide by 60
    MMmm = (abs(_dec) - abs(_dec_int)) * 100

    if _dec_int > 0:
        _latitude = _dec_int + MMmm / 60
    elif _dec_int < 0:
        _latitude = _dec_int - MMmm / 60
    elif _dec_int == 0:
        if _dec < 0:
            _latitude = -MMmm / 60
        else:
            _latitude = MMmm / 60

    if _latitude > MAXLATITUDE:
        _latitude = MAXLATITUDE
    elif _latitude < MINLATITUDE:
        _latitude = MINLATITUDE

    _latitude_100 = _latitude * 100
    _latitude_100_whole = int(_latitude_100)
    _latitude_2_decimal = _latitude_100_whole / 100
    _latitude_2_decimal_str = f"{_latitude_2_decimal:0.2f}"

    if _latitude_2_decimal == 0:  # for case when latitude is 0
        _latitude_2_decimal_str = format(_latitude_2_decimal, ".2f")

    round_latitude = "L"
    remainder = abs(_latitude_100) - abs(_latitude_100_whole)
    if remainder >= 0.5:
        round_latitude = "H"

    longitude = message[12:16]
    _longitude = struct.unpack("<i", longitude)[0]

    MINLONGITUDE = -180
    MAXLONGITUDE = 180

    _dec = _longitude * 0.000001
    _dec_int = math.trunc(_dec)
    # Minutes shift over two decimal places and divide by 60
    MMmm = (abs(_dec) - abs(_dec_int)) * 100

    if _dec_int > 0:
        _longitude = _dec_int + MMmm / 60
    elif _dec_int < 0:
        _longitude = _dec_int - MMmm / 60
    elif _dec_int == 0:
        if _dec < 0:
            _longitude = -MMmm / 60
        else:
            _longitude = MMmm / 60

    if _longitude > MAXLONGITUDE:
        _longitude = MAXLONGITUDE
    elif _longitude < MINLONGITUDE:
        _longitude = MINLONGITUDE

    _longitude_100 = _longitude * 100
    _longitude_100_whole = int(_longitude_100)
    _longitude_2_decimal = _longitude_100_whole / 100
    _longitude_2_decimal_str = f"{_longitude_2_decimal:0.2f}"

    if _longitude_2_decimal == 0:  # for case when longitude is 0
        _longitude_2_decimal_str = format(_longitude_2_decimal, ".2f")

    round_longitude = "L"
    remainder = abs(_longitude_100) - abs(_longitude_100_whole)
    if remainder >= 0.5:
        round_longitude = "H"

    message = (
        message[:24] + vehicle_id + message[26:28] + vehicle_class + message[29:]
    )  # noqa: E501

    # value of vehicle_city_id is replaced with value from CDF repository
    message = message[:26] + vehicle_city_id + message[27:]

    # replace VEH with SVR
    pub_topic = pub_topic.replace("VEH", "SVR", 1)
    # Create new Topic to send to specific CMS
    new_topic = pub_topic[:4] + pub_topic[4:].replace(
        "GTT", cms_id.lower()
    )  # replaces second GTT in string with cms_id
    new_topic += (
        "/"
        + _latitude_2_decimal_str
        + round_latitude
        + ","
        + _longitude_2_decimal_str
        + round_longitude
    )

    logging.info(f"Message: {message} being published to topic: {new_topic}")

    # Send out new Topic to CMS associated with the client_id
    response = client.publish(topic=new_topic, qos=0, payload=message)
    logging.info(
        f"Serial No. is {client_id} Agency Id is {agency_id} CMS Id is {cms_id} {response}"  # noqa: E501
    )


def insert_in_cache(
    vehicle_id, vehicle_class, vehicle_city_id, agency_id, client_id, cms_id
):  # noqa: E501
    item = {
        "ID": client_id,
        "vehicleID": vehicle_id,
        "vehicleClass": vehicle_class,
        "vehicleCityID": vehicle_city_id,
        "agencyID": agency_id,
        "CMSID": cms_id,
    }

    redis_key = f"cdf_cache:{client_id}"
    try:
        updatedRows = cache.hset(name=redis_key, mapping=item)
        logging.info(f" {updatedRows} rows written to redis sucessfully.")
    except Exception as RedisSetException:
        logging.error(f"Could not write items onto Redis: {RedisSetException}")
        raise Exception(RedisSetException)

    if not cache.expire(name=redis_key, time=1200):
        logging.error("Could not set expiry on Redis item.")
        raise Exception("Could not set expiry on Redis item.")
