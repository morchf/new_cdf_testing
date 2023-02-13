# flake8: noqa
# fmt: off
import json
import time
import os
import boto3
from CEI_Dynamo_Cache import get_vehicle_by_all_cei_vals
from CEI_Dynamo_Cache import insert_in_cache
from CEI_EVP_Activation import activate_vehicle
from CEI_EVP_IncidentProcess import post_incident
from CEI_Logging import post_log


client = boto3.client('dynamodb')
url = os.environ["CDF_URL"]


def queueHandler(event, context):
    """Dequeue event from sqs for processing

    Args:
        event (dictionary): event args
        context (content ): [description]
    """
    if event.get("Records", None) is not None:
        for record in event["Records"]:
            payload = record["body"]
            EVP_determination_process(json.loads(payload))
    else:
        EVP_determination_process(event)


def determination_executor(code):
    """Runs the specific agency evp determination boolean

    Args:
        code (string): boolean code for EVP for the determinance for the given agency
    Returns:
        i: result
    """
    #['attributes'] divider removed here until computation utility can be recovered/adapted
    code = code.replace("['attributes']",'')
    global i
    i = False
    exec("global i; i = %s" % code)
    return i


def EVP_determination_process(event):
    """Main determination process - process incident,
       update vehicle status in CDF, determine & set vehicle activation status

    Args:
        event (dictionary): incident details

    Returns:
        processResult (json string): results of all operations.
    """

    # global reference necessary for running agency boolean code
    global determine
    # print(f'Begin Dequeue Process for {event["messageId"]}')

    site_id = event["siteId"]
    agency_id = event["agencyId"]

    # Response Components
    response_code = 202
    response_body = ""

    """
    Handle Incident Tracking 
    """
    post_res = post_incident(event)
    if isinstance(type(post_res), str):
        response_code = 500
        if post_res[0] == "4":
            response_code = 400
        response = {"statusCode": response_code, "body": post_res}
        return response


    incident_value = post_res
    for i in range(len(event["incidents"])):
        if event["incidents"][i].get("units") is None:
            newUnits = []
            # print(f"No Units attached to Message - {incident_value}")

            incidentId = event["incidents"][i].get("id")
            resp = client.query(
               TableName='CEI-UnitAssignmentTracking',
               IndexName='IncidentID-index',
               ExpressionAttributeValues={
                   ':v1': {
                       'S': incidentId,
                   },
               },
               KeyConditionExpression='IncidentID = :v1',
            )
            
            for assignedUnit in resp.get("Items"):
                    print(f"assignedUnit = {assignedUnit}")
                    newUnit = {"deviceId": assignedUnit.get("CEIID").get("S")}
                    newUnits.append(newUnit)
                    unitRecord = {"units":newUnits}
                    event["incidents"][i].update(unitRecord)
            
            # if (event["incidents"][i].get("units")):
            #     print( event["incidents"][i]["units"])                

            post_log(
                site_id,
                agency_id,
                "None",
                event["messageId"],
                "Info",
                "Dequeue Determination",
                "CEI EVP Dequeue",
                response_body,
            )
        
        if not event["incidents"][i].get("units"):
            break
            
            
        for unit in event["incidents"][i]["units"]:
            device_id = unit["deviceId"]
            # print(f"\r\nFinding status for {device_id}...\r\n")
            try:
                vehicle_status = get_vehicle_by_all_cei_vals(site_id, agency_id, device_id)
                if vehicle_status is not None:
                    if not isinstance(vehicle_status, dict):
                        vehicle_status = json.loads(vehicle_status)
                        
                  
                    agency_conditional = f"{vehicle_status['CEIConditional']}"
                    # print(f"Agency Conditional Determined - {agency_conditional}")
                    response_body += f"Vehicle {device_id} found ... "
                    # print(f"Dequeue : vehicle_status = {vehicle_status}")
                    # print(f"Dequeue : incident_value = {incident_value}")
                    if not isinstance(incident_value, dict): 
                        incident_value = json.loads(incident_value)

                    # print(f"incidentStatus = {incident_value['incidentStatus']}")
                    vehicle_status["CEIIncidentStatus"] = incident_value[
                        "incidentStatus"
                    ]
                    vehicle_status[
                        "CEIIncidentStatusDateandTime"
                    ] = incident_value["incidentStatusDateTime"]
                    vehicle_status[
                        "CEIIncidentTypeCode"
                    ] = incident_value["incidentType"]
                    vehicle_status["CEIIncidentAction"] = incident_value[
                        "incidentAction"
                    ]
                    vehicle_status[
                        "CEIIncidentPriority"
                    ] = incident_value["incidentPriority"]
                    vehicle_status[
                        "CEIIncidentLocationName"
                    ] = incident_value["incidentLocationName"]
                    vehicle_status[
                        "CEIIncidentActionDateandTime"
                    ] = incident_value["incidentActionDateTime"]
                    vehicle_status[
                        "CEIIncidentLocationCrossStreet"
                    ] = incident_value["incidentLocationCrossStreet"]
                    vehicle_status[
                        "CEIIncidentLocationStreet1"
                    ] = incident_value["incidentLocationStreet1"]
                    vehicle_status[
                        "CEIIncidentLocationStreet2"
                    ] = incident_value["incidentLocationStreet2"]
                    vehicle_status[
                        "CEIIncidentLocationCity"
                    ] = incident_value["incidentLocationCity"]
                    vehicle_status[
                        "CEIIncidentLocationState"
                    ] = incident_value["incidentLocationState"]
                    vehicle_status[
                        "CEIIncidentLocationCounty"
                    ] = incident_value["incidentLocationCounty"]
                    vehicle_status[
                        "CEIIncidentLocationZip"
                    ] = incident_value["incidentLocationZip"]
                    vehicle_status[
                        "CEIIncidentLocationDirections"
                    ] = incident_value["incidentLocationDirections"]
                    vehicle_status[
                        "CEIIncidentLocationCoordinates"
                    ] = incident_value["incidentLocationCoordinates"]

                    vehicle_status["CEIUnitID"] = unit.get(
                        "unitId", vehicle_status["CEIUnitID"],
                    )
                    vehicle_status["CEIDispatchDateandTime"] = unit.get("dispatchDateTime",
                        vehicle_status["CEIDispatchDateandTime"],
                    )
                    vehicle_status["CEIUnitStatus"] = unit.get("status",
                        vehicle_status["CEIUnitStatus"],
                    )
                    vehicle_status["CEIUnitStatusDateandTime"] = unit.get("statusDateTime",
                        vehicle_status["CEIUnitStatusDateandTime"],
                    )
                    vehicle_status["CEISiteID"] = unit.get("SiteId",
                        vehicle_status["CEISiteID"],
                    )

                    if unit.get("Location"):
                        vehicle_status[
                            "CEIUnitLocationLatitudeandLongitude"
                        ] = f"{unit['location']['geometry'].get('coordinates', vehicle_status['CEIUnitLocationLatitudeandLongitude'])}"
                        vehicle_status[
                            "CEIUnitLocationDateandTime"
                        ] = unit["location"].get(
                            "updateDateTime",
                            vehicle_status["CEIUnitLocationDateandTime"],
                        )

                    vehicle_status["CEILastReferenced"] = f"{time.time()}"

                    update_call = vehicle_status
                    # print(f"Dequeue: Update Call = {update_call}")
                    
                    update_call = str(update_call).replace("'", '"').replace("|||", "'")

                    res = insert_in_cache(
                        vehicle_status["CDFID"],
                        vehicle_status["vehicleID"],
                        vehicle_status["vehicleClass"],
                        vehicle_status["vehicleCityID"],
                        vehicle_status["agencyID"],
                        vehicle_status["GTTSerial"],
                        vehicle_status["CMSID"],
                        vehicle_status["vehicleSerialNo"],
                        vehicle_status["vehicleMode"],
                        vehicle_status["CEIDeviceID"],
                        vehicle_status["CEIDispatchDateandTime"],
                        vehicle_status["CEIIncidentAction"],
                        vehicle_status["CEIIncidentActionDateandTime"],
                        vehicle_status["CEIIncidentLocationCity"],
                        vehicle_status["CEIIncidentLocationCoordinates"],
                        vehicle_status["CEIIncidentLocationCounty"],
                        vehicle_status["CEIIncidentLocationCrossStreet"],
                        vehicle_status["CEIIncidentLocationDirections"],
                        vehicle_status["CEIIncidentLocationName"],
                        vehicle_status["CEIIncidentLocationState"],
                        vehicle_status["CEIIncidentLocationStreet1"],
                        vehicle_status["CEIIncidentLocationStreet2"],
                        vehicle_status["CEIIncidentLocationZip"],
                        vehicle_status["CEIIncidentPriority"],
                        vehicle_status["CEIIncidentStatus"],
                        vehicle_status["CEIIncidentStatusDateandTime"],
                        vehicle_status["CEIIncidentTypeCode"],
                        vehicle_status["CEILastReferenced"],
                        vehicle_status["CEIUnitID"],
                        vehicle_status["CEIUnitLocationDateandTime"],
                        vehicle_status["CEIUnitLocationLatitudeandLongitude"],
                        vehicle_status["CEIUnitStatus"],
                        vehicle_status["CEIUnitStatusDateandTime"],
                        vehicle_status["CEIUnitTypeID"],
                        vehicle_status["CEIVehicleActive"],
                        vehicle_status["CEIConditional"],
                        vehicle_status["AgencyName"],
                        vehicle_status["SiteName"],
                        vehicle_status["CEIAgencyName"],
                        vehicle_status["RegionGUID"],
                        vehicle_status["CEISiteID"]
                        )
                    # print(f"dequeue: insert response = {res}")
                
                    response_body += f"Updated  {device_id} status... "
                    # print("Attempting Determinance...")
                    determine = vehicle_status
                    determinance_result = determination_executor(agency_conditional)
                    # print(f"determinance_result = {determinance_result}")
                    response_body += f"Priority Set to {determinance_result}... "
                    
                    gttSerialNum =  vehicle_status["GTTSerial"]
                    

                    activate_vehicle(
                        site_id,
                        agency_id,
                        unit["deviceId"],
                        gttSerialNum,
                        event["messageId"],
                        determinance_result,
                    )

                    # update_action = f"devices/{device_id}"
                    # update_url = f"{url}/{update_action}"

                    vehicle_status["CEILastReferenced"] = f"{time.time()}"
                    vehicle_status["CEIVehicleActive"] = determinance_result
                    # print(f"Dequeue: determinance_result = {determinance_result}")
                    
                    insert_in_cache(
                        vehicle_status["CDFID"],
                        vehicle_status["vehicleID"],
                        vehicle_status["vehicleClass"],
                        vehicle_status["vehicleCityID"],
                        vehicle_status["agencyID"],
                        vehicle_status["GTTSerial"],
                        vehicle_status["CMSID"],
                        vehicle_status["vehicleSerialNo"],
                        vehicle_status["vehicleMode"],
                        vehicle_status["CEIDeviceID"],
                        vehicle_status["CEIDispatchDateandTime"],
                        vehicle_status["CEIIncidentAction"],
                        vehicle_status["CEIIncidentActionDateandTime"],
                        vehicle_status["CEIIncidentLocationCity"],
                        vehicle_status["CEIIncidentLocationCoordinates"],
                        vehicle_status["CEIIncidentLocationCounty"],
                        vehicle_status["CEIIncidentLocationCrossStreet"],
                        vehicle_status["CEIIncidentLocationDirections"],
                        vehicle_status["CEIIncidentLocationName"],
                        vehicle_status["CEIIncidentLocationState"],
                        vehicle_status["CEIIncidentLocationStreet1"],
                        vehicle_status["CEIIncidentLocationStreet2"],
                        vehicle_status["CEIIncidentLocationZip"],
                        vehicle_status["CEIIncidentPriority"],
                        vehicle_status["CEIIncidentStatus"],
                        vehicle_status["CEIIncidentStatusDateandTime"],
                        vehicle_status["CEIIncidentTypeCode"],
                        vehicle_status["CEILastReferenced"],
                        vehicle_status["CEIUnitID"],
                        vehicle_status["CEIUnitLocationDateandTime"],
                        vehicle_status["CEIUnitLocationLatitudeandLongitude"],
                        vehicle_status["CEIUnitStatus"],
                        vehicle_status["CEIUnitStatusDateandTime"],
                        vehicle_status["CEIUnitTypeID"],
                        vehicle_status["CEIVehicleActive"],
                        vehicle_status["CEIConditional"],
                        vehicle_status["AgencyName"],
                        vehicle_status["SiteName"],
                        vehicle_status["CEIAgencyName"], 
                        vehicle_status["RegionGUID"],
                        vehicle_status["CEISiteID"]
                    )
                    
                else:
                    # print(f"Status for {device_id} not found")
                    response_body += f"Status for {device_id} not found... "

                post_log(
                    site_id,
                    agency_id,
                    unit["deviceId"],
                    event["messageId"],
                    "Info",
                    "Dequeue Determination",
                    "CEI EVP Dequeue",
                    response_body,
                )

            except Exception as e:
                print(f"dequeue: Error - {e}")
                response_body += f"Error on {device_id} : {e} ... "
                post_log(
                    site_id,
                    agency_id,
                    unit["deviceId"],
                    event["messageId"],
                    "Error",
                    "Dequeue Determination",
                    "CEI EVP Dequeue",
                    response_body,
                )
                response_code = 500

    return {"statusCode": response_code, "body": response_body}
