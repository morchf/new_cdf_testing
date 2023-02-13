import json


def get_status_data(event, lambda_context):
    """Returns number of intersections with normal/warning/error status."""
    agency_id = "12345"
    # agency_name = "agency1"
    with open("status_list.json") as json_file:
        status = json.load(json_file)

    stat_list = status.get(agency_id)
    normal = 0
    warning = 0
    error = 0
    for val in stat_list.values():
        if val[0] == "normal":
            normal += 1
        elif val[0] == "warning":
            warning += 1
        elif val[0] == "error":
            error += 1

    statuses = {}
    statuses["normal"] = normal
    statuses["warning"] = warning
    statuses["error"] = error
    return statuses
