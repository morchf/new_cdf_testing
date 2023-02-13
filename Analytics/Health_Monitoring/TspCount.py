import json


def get_tsp_count(event, lambda_context):
    """Returns TSP count for the intersection."""
    tsp_dict = {}
    with open("tsp_count.json") as json_file:
        info = json.load(json_file)
    agency_id = "12345"
    modem_list = info.get(agency_id)
    for intersection_id in modem_list:
        dict = {}
        dict["date"] = modem_list[intersection_id]["date"]
        dict["count"] = modem_list[intersection_id]["count"]
        tsp_dict[intersection_id] = dict
    return tsp_dict
