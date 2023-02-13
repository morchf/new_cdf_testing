import json


def get_intersection_info(event, lambda_context):
    """Returns information about the intersection."""
    info_dict = {"intersections": []}
    # Code that retrieves agencyName + ID
    # get_agencyName()/get_agencyID()
    # Code that retrieves list of intersections attatched to the agency
    with open("status_list.json") as json_file:
        status = json.load(json_file)
    agency_id = "12345"
    modem_list = status.get(agency_id)
    for intersection_id in modem_list:
        print(intersection_id)
        dict = {"lat": 0, "long": 0, "intersectionName": "", "intersectionId": ""}
        dict["lat"] = modem_list[intersection_id][1]
        dict["long"] = modem_list[intersection_id][2]
        dict["intersectionName"] = modem_list[intersection_id][3]
        dict["intersectionId"] = intersection_id
        info_dict["intersections"].append(dict)

    return info_dict
