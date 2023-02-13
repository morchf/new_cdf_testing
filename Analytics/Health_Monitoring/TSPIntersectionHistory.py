import json


def get_tsp_intersection_history(event, lambda_context):
    """Returns information about the intersection."""
    info_dict = {"data": []}
    # Code that retrieves the TSP Intersection History for an intersection
    with open("intersection_history.json") as json_file:
        tsp_intersections_list = json.load(json_file)
    intersection_id = "45th Street"
    reqsPerDay = tsp_intersections_list.get(intersection_id)
    for dailyData in reqsPerDay:
        dict = {}
        dict["date"] = dailyData["date"]
        dict["numReqs"] = dailyData["numberOfReqs"]
        info_dict["data"].append(dict)

    return info_dict
