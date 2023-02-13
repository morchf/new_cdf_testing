import json
import datetime


def create_messages(info):
    """Creates messages by iterating over the list of devices and other information received.

    Args:
        information_to_decode (dict): information to decode and create messages.

    Returns:
        _type_: json string of all messages that'll be dumped on a Queue.
    """
    devices = info.get("devices")
    request = info.get("request")
    messages = []
    for device in devices:
        message = {}
        message["request"] = request
        if request == "changepreemption":
            message["agency_guid"] = info.get("agency_guid")
            message["preemption_value"] = devices.get(device)
            message["device_id"] = device
        elif request == "importvehicles":
            message["vehicle"] = device
            message["agency_region"] = info.get("agency_region")
            message["agency_name"] = info.get("agency_name")
            message["agency_guid"] = info.get("agency_guid")
        messages.append(json.dumps(message))
    return messages


def create_report(start_timestamp, errors):
    start_time = datetime.datetime.fromtimestamp(start_timestamp).strftime(
        "%Y-%m-%d %I:%M:%S%p UTC"
    )
    error_block = "\n".join(errors)

    return f"""
    Started {start_time}

    Number of Errors: {len(errors)}

    {error_block}
    """
