import json


def get_firmware_info(event, lambda_context):
    """Returns firmware info of the intersection modems."""
    firmware_dict = {}
    with open("firmware_info.json") as json_file:
        infos = json.load(json_file)

    agency_id = "12345"
    modem_list = infos.get(agency_id)

    for intersection_id in modem_list:
        dict = {}
        dict["currentFirmwareVersion"] = modem_list[intersection_id][
            "currentFirmwareVersion"
        ]
        dict["historyFirmwareVersion"] = modem_list[intersection_id][
            "historyFirmwareVersion"
        ]
        firmware_dict[intersection_id] = dict

    return firmware_dict
