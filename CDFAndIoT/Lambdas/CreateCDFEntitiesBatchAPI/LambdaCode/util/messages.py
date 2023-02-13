import json
import functools
import datetime


def create_path(*args):
    return "/" + "/".join([s.lower() for s in args])


ENTITY_TYPE_ORDER = [
    "region",
    "agency",
    "vehiclev2",
    "communicator",
]


def sort_by_type_order(x, y):
    return ENTITY_TYPE_ORDER.index(
        json.loads(x)["templateId"]
    ) - ENTITY_TYPE_ORDER.index(json.loads(y)["templateId"])


NULL_GUID = "NULL_GUID"
NULL_CA = "NULL_CA"
NULL_CERT = "NULL_CERT"


def create_json(record):
    if record.get("region") == "region":
        return {
            "attributes": {"caCertId": NULL_CA, "regionGUID": NULL_GUID},
            "category": "group",
            "templateId": "region",
            "description": record.get("description", ""),
            "name": record.get("name"),
            "parentPath": "/",
            "groupPath": create_path(record["name"]),
        }

    elif record.get("agency") == "agency":
        return {
            "description": record.get("description", ""),
            "attributes": {
                "CMSId": record.get("CMSId", ""),
                "city": record.get("city", ""),
                "state": record.get("state", ""),
                "timezone": record.get("timezone", ""),
                "agencyCode": record.get("agencyCode", 0),
                "agencyID": record.get("agencyID", NULL_GUID),
                "caCertId": record.get("caCertId", NULL_CA),
                "vpsCertId": record.get("vpsCertId", NULL_CERT),
                "priority": record.get("priority", ""),
            },
            "category": "group",
            "templateId": "agency",
            "name": record.get("name", ""),
            "groupPath": create_path(record.get("region", ""), record.get("name", "")),
            "parentPath": create_path(record.get("region", "")),
        }

    elif record.get("vehiclev2") == "vehiclev2":
        return {
            "description": record.get("description", ""),
            "attributes": {
                "name": record.get("name", ""),
                "type": record.get("type", "Unassigned"),
                "class": record.get("class", 10),
                "VID": record.get("VID", 0),
                "priority": record.get("priority", ""),
                "uniqueId": record.get("uniqueId", NULL_GUID),
            },
            "category": "device",
            "templateId": "vehiclev2",
            "state": "active",
            "deviceId": NULL_GUID,
            "groups": {
                "ownedby": [
                    create_path(record.get("region", ""), record.get("agency", ""))
                ]
            },
        }

    elif record.get("communicator") == "communicator":
        return {
            "description": record.get("description", ""),
            "attributes": {
                "gttSerial": record.get("gttSerial", ""),
                "serial": record.get("serial", ""),
                "addressMAC": record.get("addressMAC", ""),
                "addressLAN": record.get("addressLAN", ""),
                "addressWAN": record.get("addressWAN", ""),
                "IMEI": record.get("IMEI", ""),
                "make": record.get("make", ""),
                "model": str(record.get("model", "")),
                "devCertId": record.get("devCertId", NULL_CERT),
                "uniqueId": record.get("uniqueId", NULL_GUID),
            },
            "category": "device",
            "templateId": "communicator",
            "state": "active",
            "deviceId": record.get("serial", ""),
            "groups": {
                "ownedby": [
                    create_path(record.get("region", ""), record.get("agency", ""))
                ]
            },
            "vehicle": record.get("vehicle", ""),
        }

    elif record.get("phaseselector") == "phaseselector":
        return {
            "deviceId": record.get("deviceId", ""),
            "attributes": {
                "description": record.get("description", ""),
                "gttSerial": record.get("gttSerial", ""),
                "serial": record.get("serial", ""),
                "addressMAC": record.get("addressMAC", ""),
                "addressLAN": record.get("addressLAN", ""),
                "addressWAN": record.get("addressWAN", ""),
                "make": record.get("make", ""),
                "model": record.get("model", ""),
            },
            "category": "device",
            "templateId": "phaseselector",
            "state": "active",
            "groups": {"ownedby": create_path(record["region"], record["agency"])},
        }

    elif record.get("location") == "location":
        name = None
        if "displayName" in record:
            name = record["displayName"]
        if "name" in record:
            name = record["name"]

        return {
            "deviceId": record.get("deviceId", ""),
            "attributes": {
                "description": record.get("description", ""),
                "address": record.get("address", ""),
                "latitude": record.get("latitude", ""),
                "longitude": record.get("longitude", ""),
                "locationId": record.get("locationId", ""),
                "name": name,
            },
            "category": "group",
            "templateId": "location",
            "name": record.get("locationId", ""),
            "parentPath": create_path(
                record.get("region", ""), record.get("agency", "")
            ),
            "groups": create_path(
                record.get("region", ""),
                record.get("agency", ""),
                record.get("locationId", ""),
            ),
        }

    else:
        raise Exception("Error invalid input data.")


def create_messages(records):
    messages = [json.dumps(create_json(record)) for record in records]
    return list(sorted(messages, key=functools.cmp_to_key(sort_by_type_order)))


def create_report(start_timestamp, errors):
    start_time = datetime.datetime.fromtimestamp(start_timestamp).strftime(
        "%Y-%m-%d %I:%M:%S%p UTC"
    )

    error_block = ""
    for error in errors:
        error_dict = json.loads(error)
        error_block += error_dict["error"] + "\n" + error_dict["entity"] + "\n\n"

    return f"""
    Started {start_time}

    Number of Errors: {len(errors)}

    {error_block}
    """
