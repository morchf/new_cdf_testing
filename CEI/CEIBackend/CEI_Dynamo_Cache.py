import json
import boto3
import time
import os
from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session
from botocore.auth import SigV4Auth
from boto3.dynamodb.conditions import Key, Attr

url = os.environ["CDF_URL"]
headers = {
    "Accept": "application/vnd.aws-cdf-v2.0+json",
    "Content-Type": "application/vnd.aws-cdf-v2.0+json",
}

dynamodb = boto3.resource("dynamodb")
dyanmoClient = boto3.client("dynamodb", region_name=os.environ["AWS_REGION"])
table = dynamodb.Table("CEI-CDF-Cache")


def send_request(url, method, region_name, params=None, headers=None):
    """Send request to CDF API for data
    Args:
        url (STR): request address
        method (STR): request method
        region_name (str): AWS Region
        params (json, optional): data to request. Defaults to None.
        headers (json, optional): header configuration. Defaults to None.
    Returns:
        json: request response
    """
    request = AWSRequest(method=method.upper(), url=url, data=params, headers=headers)
    SigV4Auth(boto3.Session().get_credentials(), "execute-api", region_name).add_auth(
        request
    )
    return URLLib3Session().send(request.prepare()).content


def insert_in_cache(
    client_id,
    vehicle_id,
    vehicle_class,
    vehicle_city_id,
    agency_id,
    gtt_serial,
    cms_id,
    unit_id,
    vehicle_mode,
    CEI_DeviceID,
    CEI_DispatchDateandTime,
    CEI_IncidentAction,
    CEI_IncidentActionDateandTime,
    CEI_IncidentLocationCity,
    CEI_IncidentLocationCoordinates,
    CEI_IncidentLocationCounty,
    CEI_IncidentLocationCrossStreet,
    CEI_IncidentLocationDirections,
    CEI_IncidentLocationName,
    CEI_IncidentLocationState,
    CEI_IncidentLocationStreet1,
    CEI_IncidentLocationStreet2,
    CEI_IncidentLocationZip,
    CEI_IncidentPriority,
    CEI_IncidentStatus,
    CEI_IncidentStatusDateandTime,
    CEI_IncidentTypeCode,
    CEI_LastReferenced,
    CEI_UnitID,
    CEI_UnitLocationDateandTime,
    CEI_UnitLocationLatitudeandLongitude,
    CEI_UnitStatus,
    CEI_UnitStatusDateandTime,
    CEI_UnitTypeID,
    CEI_VehicleActive,
    CEI_Conditional,
    AgencyName,
    SiteName,
    CEIAgencyName,
    RegionGUID,
    CEISiteID,
    createOnly=False,
):
    current_time = int(time.time())
    item = {
        "CDFID": client_id,
        "vehicleID": vehicle_id,
        "vehicleClass": vehicle_class,
        "vehicleCityID": vehicle_city_id,
        "agencyID": agency_id,
        "GTTSerial": gtt_serial,
        "CMSID": cms_id,
        "vehicleSerialNo": unit_id,
        "vehicleMode": vehicle_mode,
        "CEIDeviceID": CEI_DeviceID,
        "CEIDispatchDateandTime": CEI_DispatchDateandTime,
        "CEIIncidentAction": CEI_IncidentAction,
        "CEIIncidentActionDateandTime": CEI_IncidentActionDateandTime,
        "CEIIncidentLocationCity": CEI_IncidentLocationCity,
        "CEIIncidentLocationCoordinates": CEI_IncidentLocationCoordinates,
        "CEIIncidentLocationCounty": CEI_IncidentLocationCounty,
        "CEIIncidentLocationCrossStreet": CEI_IncidentLocationCrossStreet,
        "CEIIncidentLocationDirections": CEI_IncidentLocationDirections,
        "CEIIncidentLocationName": CEI_IncidentLocationName,
        "CEIIncidentLocationState": CEI_IncidentLocationState,
        "CEIIncidentLocationStreet1": CEI_IncidentLocationStreet1,
        "CEIIncidentLocationStreet2": CEI_IncidentLocationStreet2,
        "CEIIncidentLocationZip": CEI_IncidentLocationZip,
        "CEIIncidentPriority": CEI_IncidentPriority,
        "CEIIncidentStatus": CEI_IncidentStatus,
        "CEIIncidentStatusDateandTime": CEI_IncidentStatusDateandTime,
        "CEIIncidentTypeCode": CEI_IncidentTypeCode,
        "CEILastReferenced": CEI_LastReferenced,
        "CEIUnitID": CEI_UnitID,
        "CEIUnitLocationDateandTime": CEI_UnitLocationDateandTime,
        "CEIUnitLocationLatitudeandLongitude": CEI_UnitLocationLatitudeandLongitude,
        "CEIUnitStatus": CEI_UnitStatus,
        "CEIUnitStatusDateandTime": CEI_UnitStatusDateandTime,
        "CEIUnitTypeID": CEI_UnitTypeID,
        "CEIVehicleActive": CEI_VehicleActive,
        "CEIConditional": CEI_Conditional,
        "AgencyName": AgencyName,
        "SiteName": SiteName,
        "CEIAgencyName": CEIAgencyName,
        "RegionGUID": RegionGUID,
        "CEISiteID": CEISiteID,
        "TTL": current_time + 14400,
    }

    for val in item.keys():
        if isinstance(item[val], str):
            item[val] = item[val].replace("|||", "'")
    if createOnly:
        dynamo_item = table.query(
            ConsistentRead=True, KeyConditionExpression=Key("CDFID").eq(client_id)
        )
        if len(dynamo_item.get("Items")) == 0:
            table.put_item(Item=item)
    else:
        table.put_item(Item=item)


def get_vehicle_by_all_cei_vals(ceisiteid, ceiagencyid, ceiunitid, createOnly=False):
    dynamo_item = table.scan(
        FilterExpression=Attr("CEIDeviceID").eq(ceiunitid)
        & Attr("CEIAgencyName").eq(ceiagencyid)
        & Attr("CEISiteID").eq(ceisiteid)
    )

    if len(dynamo_item.get("Items")) > 0:
        return dynamo_item.get("Items")[0]

    else:
        agencyInfo = CDF_get_agency_by_CEI_IDs(ceisiteid, ceiagencyid)[0]
        # print(f"cache: agencyData = {agencyInfo}")
        site_name = agencyInfo.get("parentPath").replace("/", "")
        region_info = CDF_get_region(site_name)
        vehicleInfo = CDF_get_vehicle_by_ceiunitid(ceiunitid)
        # print(f"cache: vehicleInfo = {vehicleInfo}")
        comDeviceId = ""
        if vehicleInfo["devices"].get("out"):
            comDeviceId = vehicleInfo["devices"]["out"]["installedat"][0]
        else:
            comDeviceId = vehicleInfo["devices"]["in"]["installedat"][0]
        comInfo = CDF_get_device(comDeviceId)
        # print(f"cache: comInfo = {comInfo}")
        vehicleMode = 0
        if vehicleInfo["attributes"]["priority"] == "High":
            vehicleMode = 1
        # print(f"cache: agencyInfo = {agencyInfo}")
        insert_in_cache(
            comInfo.get("deviceId"),
            vehicleInfo["attributes"]["VID"],
            vehicleInfo["attributes"]["class"],
            agencyInfo["attributes"]["agencyCode"],
            agencyInfo["attributes"]["agencyID"],
            comInfo["attributes"]["gttSerial"],
            agencyInfo["attributes"]["agencyGUID"],
            calc_unit_id(comInfo["attributes"]["addressMAC"]),
            vehicleMode,
            ceiunitid,
            vehicleInfo["attributes"]["CEIDispatchDateandTime"],
            vehicleInfo["attributes"]["CEIDispatchDateandTime"],
            vehicleInfo["attributes"]["CEIIncidentActionDateandTime"],
            vehicleInfo["attributes"]["CEIIncidentLocationCity"],
            vehicleInfo["attributes"]["CEIIncidentLocationCoordinates"],
            vehicleInfo["attributes"]["CEIIncidentLocationCounty"],
            vehicleInfo["attributes"]["CEIIncidentLocationCrossStreet"],
            vehicleInfo["attributes"]["CEIIncidentLocationDirections"],
            vehicleInfo["attributes"]["CEIIncidentLocationName"],
            vehicleInfo["attributes"]["CEIIncidentLocationState"],
            vehicleInfo["attributes"]["CEIIncidentLocationStreet1"],
            vehicleInfo["attributes"]["CEIIncidentLocationStreet2"],
            vehicleInfo["attributes"]["CEIIncidentLocationZip"],
            vehicleInfo["attributes"]["CEIIncidentPriority"],
            vehicleInfo["attributes"]["CEIIncidentStatus"],
            vehicleInfo["attributes"]["CEIIncidentStatusDateandTime"],
            vehicleInfo["attributes"]["CEIIncidentTypeCode"],
            vehicleInfo["attributes"]["CEILastReferenced"],
            vehicleInfo["attributes"]["CEIUnitID"],
            vehicleInfo["attributes"]["CEIUnitLocationDateandTime"],
            vehicleInfo["attributes"]["CEIUnitLocationLatitudeandLongitude"],
            vehicleInfo["attributes"]["CEIUnitStatus"],
            vehicleInfo["attributes"]["CEIUnitStatusDateandTime"],
            vehicleInfo["attributes"]["CEIUnitTypeID"],
            vehicleInfo["attributes"]["CEIVehicleActive"],
            agencyInfo["attributes"]["CEIEVPConditional"],
            agencyInfo["name"],
            site_name,
            ceiagencyid,
            region_info["attributes"]["regionGUID"],
            ceisiteid,
            createOnly,
        )

        dynamo_item = table.scan(
            FilterExpression=Attr("CEIDeviceID").eq(ceiunitid)
            & Attr("CEIAgencyName").eq(ceiagencyid)
            & Attr("CEISiteID").eq(ceisiteid)
        )

        if len(dynamo_item.get("Items")) > 0:
            # print(dynamo_item.get("Items")[0])
            return dynamo_item.get("Items")[0]

        else:
            return "ERROR - Unable to find/populate cache"


def get_vehicle_by_SN(sn, rescan=False):
    dynamo_item = table.scan(FilterExpression=Attr("CDFID").eq(sn))
    if len(dynamo_item.get("Items")) > 0:
        return dynamo_item.get("Items")[0]
    else:
        if not rescan:
            get_CDF_com_info(sn, createOnly=False)
            return get_vehicle_by_SN(sn, True)
        return None


def get_agency_name(site_id, agency_id):
    dynamo_item = table.scan(
        FilterExpression=Attr("AgencyName").eq(agency_id.lower())
        & Attr("SiteName").eq(site_id.lower())
    )

    if len(dynamo_item.get("Items")) > 0:
        return dynamo_item.get("Items")[0]["CEIAgencyName"]
    else:
        results = CDF_get_agency(site_id, agency_id)
        if results is not None:
            return results["attributes"]["CEIAgencyName"]


def calc_unit_id(mac):
    mac = mac.replace(":", "")[-6:]
    unit_id_binary = bin(int(mac, 16))[2:].zfill(24)
    # unit_id = 0x800000 | mac_address
    orrer = f"{8388608:024b}"
    orred_unit_id = ""

    for i in range(0, 24):
        orred_unit_id += str(int(orrer[i]) | int(unit_id_binary[i]))

    return int(orred_unit_id, 2)


def get_CDF_com_info(comName, createOnly=False):

    comInfo = CDF_get_device(comName)
    cdf_site_id = comInfo["groups"]["out"]["ownedby"][0].split("/")[1]
    cdf_vehicle_id = comInfo["devices"]["in"]["installedat"][0]

    region_info = CDF_get_region(cdf_site_id)
    vehicleInfo = CDF_get_device(cdf_vehicle_id)
    cdf_agency_id = vehicleInfo["groups"]["out"]["ownedby"][0].split("/")[2]

    agencyInfo = CDF_get_agency(cdf_site_id, cdf_agency_id)

    vehicleMode = 0
    if vehicleInfo["attributes"]["priority"] == "High":
        vehicleMode = 1

    insert_in_cache(
        comName,
        vehicleInfo["attributes"]["VID"],
        vehicleInfo["attributes"]["class"],
        agencyInfo["attributes"]["agencyCode"],
        agencyInfo["attributes"]["agencyID"],
        comInfo["attributes"]["gttSerial"],
        agencyInfo["attributes"]["agencyGUID"],
        calc_unit_id(comInfo["attributes"]["addressMAC"]),
        vehicleMode,
        vehicleInfo["attributes"]["CEIDeviceID"],
        vehicleInfo["attributes"]["CEIDispatchDateandTime"],
        vehicleInfo["attributes"]["CEIDispatchDateandTime"],
        vehicleInfo["attributes"]["CEIIncidentActionDateandTime"],
        vehicleInfo["attributes"]["CEIIncidentLocationCity"],
        vehicleInfo["attributes"]["CEIIncidentLocationCoordinates"],
        vehicleInfo["attributes"]["CEIIncidentLocationCounty"],
        vehicleInfo["attributes"]["CEIIncidentLocationCrossStreet"],
        vehicleInfo["attributes"]["CEIIncidentLocationDirections"],
        vehicleInfo["attributes"]["CEIIncidentLocationName"],
        vehicleInfo["attributes"]["CEIIncidentLocationState"],
        vehicleInfo["attributes"]["CEIIncidentLocationStreet1"],
        vehicleInfo["attributes"]["CEIIncidentLocationStreet2"],
        vehicleInfo["attributes"]["CEIIncidentLocationZip"],
        vehicleInfo["attributes"]["CEIIncidentPriority"],
        vehicleInfo["attributes"]["CEIIncidentStatus"],
        vehicleInfo["attributes"]["CEIIncidentStatusDateandTime"],
        vehicleInfo["attributes"]["CEIIncidentTypeCode"],
        vehicleInfo["attributes"]["CEILastReferenced"],
        vehicleInfo["attributes"]["CEIUnitID"],
        vehicleInfo["attributes"]["CEIUnitLocationDateandTime"],
        vehicleInfo["attributes"]["CEIUnitLocationLatitudeandLongitude"],
        vehicleInfo["attributes"]["CEIUnitStatus"],
        vehicleInfo["attributes"]["CEIUnitStatusDateandTime"],
        vehicleInfo["attributes"]["CEIUnitTypeID"],
        vehicleInfo["attributes"]["CEIVehicleActive"],
        agencyInfo["attributes"]["CEIEVPConditional"],
        cdf_agency_id,
        cdf_site_id,
        agencyInfo["attributes"]["CEIAgencyName"],
        region_info["attributes"]["regionGUID"],
        agencyInfo["attributes"]["CEISiteIDGuid"],
        createOnly,
    )

    return


def CDF_get_agency(site_name, agency_name):
    site_name = site_name.lower()
    agency_name = agency_name.lower()
    request_url = f"{url}/groups/%2F{site_name}%2F{agency_name}"
    # print(f"cache: CDF_get_agency request_url = {request_url}")
    requested_info = send_request(
        request_url, "GET", os.environ["AWS_REGION"], headers=headers
    )
    if requested_info is not None:
        requested_info = json.loads(requested_info)
    return requested_info


def CDF_get_device(device_id):
    device_id = device_id
    request_url = f"{url}/devices/{device_id}"
    # print(f"cache: pull_com_from_CDF request_url = {request_url}")
    requested_info = send_request(
        request_url, "GET", os.environ["AWS_REGION"], headers=headers
    )
    requested_info = json.loads(requested_info)
    # print(f"cache : pull_com_from_CDF requested_info = {requested_info}")
    return requested_info


def CDF_get_region(site_name):
    site_name = site_name.lower()
    request_url = f"{url}/groups/%2F{site_name}"
    code = send_request(request_url, "GET", os.environ["AWS_REGION"], headers=headers)
    dataRegion = json.loads(code)
    return dataRegion


def CDF_get_agency_by_CEI_IDs(ceiSiteID, ceiAgencyID):
    request_url = f"{url}/search?type=ceiagency&eq=CEIAgencyName%3A{ceiAgencyID}&eq=CEISiteIDGuid%3A{ceiSiteID}"
    # print(f"cache: CDF_get_agency_by_CEI_IDs request_url = {request_url}")
    agency_data = send_request(
        request_url, "GET", os.environ["AWS_REGION"], headers=headers
    )
    agency_results = json.loads(agency_data).get("results")
    if agency_results:
        return agency_results
    else:
        raise Exception(f"Error - Agency {ceiAgencyID} for site {ceiSiteID} not found")


def CDF_get_vehicle_by_ceiunitid(ceiUnitId):
    request_url = f"{url}/search?type=ceivehiclev2&eq=CEIDeviceID%3A{ceiUnitId}"
    # print(f"cache: request_url = {request_url}")
    vehicle_data = send_request(
        request_url, "GET", os.environ["AWS_REGION"], headers=headers
    )
    # print(f"cache: vehicle_data = {vehicle_data}")
    vehicle_results = json.loads(vehicle_data).get("results")
    # print(f"cache: vehicle_results = {vehicle_results}")
    # Querty calls do NOT get device associations for... some reason.
    deviceId = vehicle_results[0].get("deviceId")
    print(f"cache: deviceId = {deviceId}")
    resultsWithSubdDevice = CDF_get_device(deviceId)
    # print(f"cache: resultsWithSubdDevice = {resultsWithSubdDevice}")
    # print(f"cache: deviceId = {deviceId}")
    return resultsWithSubdDevice


def delete_cache_entry(ceiUnitId):
    """Removes an item from the cache to default it's values
    used when a vehicle is assigned to a different incident.
    Args:
        ceiUnitId (_type_): identifier of cache val
    """
    table.delete_item(Key={"CDFID": ceiUnitId})
