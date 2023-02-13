import boto3
import time
import logging
from boto3.dynamodb.conditions import Key
from CEI_Logging import post_log
from CEI_Dynamo_Cache import delete_cache_entry

dynamodb = boto3.resource("dynamodb")


def post_incident(event):
    """Record the incoming incident details to dynamodb

    Args:
        event (dictionary): Incident Event details: used for storing/updating incident record

    Returns:
        response(string): results of all operations
    """
    print("dequeue incident: begin incident processing...")
    logging.info("Incident Tracking...")
    """
    process incidents within events - "None" used as CDF friendly default.
    """
    for i in range(len(event["incidents"])):
        # incident values to be updated
        crossStreet = "None"
        street1 = "None"
        street2 = "None"
        city = "None"
        state = "None"
        county = "None"
        zipCode = "None"
        directions = "None"
        coordinates = "None"
        try:
            inc_id = event["incidents"][i].get("id", "None")
            status = event["incidents"][i].get("status", "None")
            statusDateTime = event["incidents"][i].get("statusDateTime", "None")
            typeCode = event["incidents"][i].get("type", "None")
            priority = event["incidents"][i].get("priority", "None")
            action = event["incidents"][i].get("action", "None")
            actionDateTime = event["incidents"][i].get("actionDateTime", "None")
            locationDict = event["incidents"][i].get("location", {})
            locationName = locationDict.get("name", "None")
            locAddrDict = locationDict.get("address", {})
            if len(locAddrDict) > 0:
                crossStreet = locAddrDict.get("crossStreet", "None")
                street1 = locAddrDict.get("street1", "None")
                street2 = locAddrDict.get("street2", "None")
                city = locAddrDict.get("city", "None")
                state = locAddrDict.get("state", "None")
                county = locAddrDict.get("county", "None")
                zipCode = locAddrDict.get("zip", "None")
                directions = locAddrDict.get("directions", "None")
                if len(locationDict["geometry"]) > 0:
                    coordinates = (
                        f"{ locationDict['geometry'].get('Coordinates','None') }"
                    )
        except Exception as e:
            post_log(
                event.get("siteId", "None"),
                event.get("agencyId", "None"),
                "None",
                event.get("messageId", "None"),
                "Error",
                "Incident Processing",
                "New Incident",
                f"400 Error - Incident Processing failed (parsing) {e}... ",
            )
            print(f"400 Error - Incident Processing failed (parsing) {e}... ")
            return f"400 Error - Incident Processing failed (parsing) {e}... "

    # Get Units
    unitList = ""
    if event["incidents"][i].get("units"):
        units = event["incidents"][i].get("units")
        for unit in units:
            unitAssociation(unit.get("deviceId"), event["incidents"][i].get("id"))

    # incident declaration - "None" used for CDF purposes
    incident = {
        "IncidentID": (inc_id if inc_id != "" else "None"),
        "incidentStatus": (status if status != "" else "None"),
        "incidentStatusDateTime": (statusDateTime if statusDateTime != "" else "None"),
        "incidentType": (typeCode if typeCode != "" else "None"),
        "incidentPriority": (priority if priority != "" else "None"),
        "incidentActionDateTime": (actionDateTime if actionDateTime != "" else "None"),
        "incidentLocationName": str(
            locationName if locationName != "" else "None"
        ).replace("'", "|||"),
        "incidentLocationCrossStreet": str(
            crossStreet if crossStreet != "" else "None"
        ).replace("'", "|||"),
        "incidentLocationStreet1": str(street1 if street1 != "" else "None").replace(
            "'", "|||"
        ),
        "incidentLocationStreet2": str(street2 if street2 != "" else "None").replace(
            "'", "|||"
        ),
        "incidentLocationCity": str(city if city != "" else "None").replace("'", "|||"),
        "incidentLocationState": (state if state != "" else "None"),
        "incidentLocationCounty": str(county if county != "" else "None").replace(
            "'", "|||"
        ),
        "incidentLocationZip": (zipCode if zipCode != "" else "None"),
        "incidentLocationDirections": str(
            directions if directions != "" else "None"
        ).replace("'", "|||"),
        "incidentLocationCoordinates": (coordinates if coordinates != "" else "None"),
        "incidentAction": (action if action != "" else "None"),
        "incidentUnits": (unitList if unitList != "" else "None"),
        "ceittl": int(time.time()) + 6000,
    }

    print(f"dequeue incident: incident to be processed...{incident}")
    for key, value in incident.items():
        logging.info(f"{key} {value}")
        if value == "":
            value = "None"

    response = "DynamoDB Failure"
    try:
        table = dynamodb.Table("CEI-IncidentTracking")
        response = table.query(
            ConsistentRead=True, KeyConditionExpression=Key("IncidentID").eq(inc_id)
        )
        # print(f"dequeue incident: dynamo query response = {response}")
        if response.get("Count") != 1:
            response = "IncidentID not found - recording... "
            print("dequeue incident: IncidentID not found - recording...")
            try:
                table.put_item(Item=incident)
                # print(f"dequeue incident: put_result = {put_result}")
            except Exception as e:
                print(
                    f"dequeue incident: 400 Error - Incident Processing failed (put) {e}... "
                )
                response = f"400 Error - Incident Processing failed (put) {e}... "
                logging.error(response)
                post_log(
                    event.get("siteId", "None"),
                    event.get("agencyId", "None"),
                    "None",
                    event.get("messageId", "None"),
                    "Error",
                    "Incident Processing",
                    "New Incident",
                    response,
                )
                return response
            response = incident
            post_log(
                event.get("siteId", "None"),
                event.get("agencyId", "None"),
                "None",
                event.get("messageId", "None"),
                "Info",
                "Incident Processing",
                "New Incident",
                response,
            )
        else:
            logging.info("incident ID found - updating...")
            # print("dequeue incident:incident ID found - updating...")
            try:
                responseItems = response.get("Items")[0]
                for k in incident:
                    logging.info(f"{incident[k]} vs {responseItems[k]}")
                    if incident[k] == "None":
                        incident[k] = responseItems[k]
                        logging.info(f"assigned to {incident[k]}")

                for key, value in incident.items():
                    if incident[key] != "None":
                        responseItems[key] = incident[key]

                """
                Update incident within dynamoDB
                """
                response = table.update_item(
                    Key={
                        "IncidentID": incident["IncidentID"],
                    },
                    UpdateExpression="SET ceittl = :val0, incidentStatus = :val1, incidentStatusDateTime = :val2,  incidentType = :val3, incidentPriority = :val4,  incidentActionDateTime = :val5,  incidentLocationName = :val6,  incidentLocationCrossStreet = :val7,  incidentLocationStreet1 = :val8,  incidentLocationStreet2 = :val9,  incidentLocationCity = :val10,  incidentLocationState = :val11,  incidentLocationCounty = :val12,  incidentLocationZip = :val13,  incidentLocationDirections = :val14,  incidentLocationCoordinates = :val15, incidentAction = :val16, incidentUnits = :val17",
                    ExpressionAttributeValues={
                        ":val0": incident["ceittl"],
                        ":val1": incident["incidentStatus"],
                        ":val2": incident["incidentStatusDateTime"],
                        ":val3": incident["incidentType"],
                        ":val4": incident["incidentPriority"],
                        ":val5": incident["incidentActionDateTime"],
                        ":val6": incident["incidentLocationName"],
                        ":val7": incident["incidentLocationCrossStreet"],
                        ":val8": incident["incidentLocationStreet1"],
                        ":val9": incident["incidentLocationStreet2"],
                        ":val10": incident["incidentLocationCity"],
                        ":val11": incident["incidentLocationState"],
                        ":val12": incident["incidentLocationCounty"],
                        ":val13": incident["incidentLocationZip"],
                        ":val14": incident["incidentLocationDirections"],
                        ":val15": incident["incidentLocationCoordinates"],
                        ":val16": incident["incidentAction"],
                        ":val17": incident["incidentUnits"],
                    },
                    ReturnValues="UPDATED_NEW",
                )
                logging.info(f"Update response is {response}")
                # print(f"dequeue incident: Update response is {response}")
                response = incident
                post_log(
                    event.get("siteId", "None"),
                    event.get("agencyId", "None"),
                    "None",
                    event.get("messageId", "None"),
                    "Info",
                    "Incident Processing",
                    "Update Incident",
                    f"Update response is {response}",
                )
            except Exception as e:
                print(f"dequeue: 400 Error - Incident Processing failed {e}... ")
                logging.error(response)
                post_log(
                    event.get("siteId", "None"),
                    event.get("agencyId", "None"),
                    "None",
                    event.get("messageId", "None"),
                    "Error",
                    "Incident Processing",
                    "Update Incident",
                    response,
                )
                return f"400 Error - Incident Processing failed (update) {e}... "
    except Exception as e:
        response = f"400 Error - Incident Processing failed {e}... "
        print(f"dequeue: 400 Error - Incident Processing failed {e}... ")
    return response


def unitAssociation(ceiid, incidentid):
    table = dynamodb.Table("CEI-UnitAssignmentTracking")
    response = table.query(
        ConsistentRead=True, KeyConditionExpression=Key("CEIID").eq(ceiid)
    )
    ttl = int(time.time()) + 6000
    if response.get("Count") != 1:
        response = "CEIID not found - recording... "
        try:
            entry = {"CEIID": ceiid, "IncidentID": incidentid, "CEITTL": ttl}
            table.put_item(Item=entry)
            # print(f"dequeue unit association: put_result = {put_result}")
        except Exception as e:
            print(f"dequeue: 400 Error - Unit Association failed {e}... ")
            logging.error(response)
    else:
        if response.get("IncidentID") == incidentid:
            # print(f"dequeue unit association: unit record up to date")
            return

        response = table.update_item(
            Key={
                "CEIID": ceiid,
            },
            UpdateExpression="SET IncidentID = :val0, CEITTL = :val1",
            ExpressionAttributeValues={":val0": incidentid, ":val1": ttl},
            ReturnValues="UPDATED_NEW",
        )

        delete_cache_entry(ceiid)
