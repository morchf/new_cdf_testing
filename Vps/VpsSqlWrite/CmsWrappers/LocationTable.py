import datetime
import uuid
import logging

logging.basicConfig(level=logging.DEBUG)

LOCATION_QUERY_TEMPLATE_MINIMAL = """
            DECLARE @Id UNIQUEIDENTIFIER;
            EXEC [OpticomManagement].[dbo].[LocationInsert] @RegionId=?,
                                                            @LocationName=?,
                                                            @LocationDescription=?,
                                                            @Address=?,
                                                            @City=?,
                                                            @StateProvince=?,
                                                            @PostalCode=?,
                                                            @CreatedDateTime=?,
                                                            @ModifiedDateTime=?,
                                                            @CreatedUserId=?,
                                                            @ModifiedUserId=?,
                                                            @IsDeleted=?,
                                                            @IsActive=?,
                                                            @Latitude=?,
                                                            @Longitude=?,
                                                            @Elevation=?,
                                                            @LocationNumber=?,
                                                            @LocationType=?,
                                                            @LocationConfigXml=?,
                                                            @IsShared=?,
                                                            @AllianceId=?,
                                                            @ForeignId=?,
                                                            @ForeignRegionId=?,
"""
CMS_VERSION_6_8_0 = (
    "6.8.0",
    """                                                            @LocationId=@Id OUTPUT;
            SELECT @Id as id;""",
)
CMS_VERSION_6_10_0 = (
    "6.10.0",
    """                                                            @ControllerId=?,
                                                            @LocationId=@Id OUTPUT;
            SELECT @Id as id;""",
)
CMS_VERSIONS = [CMS_VERSION_6_10_0, CMS_VERSION_6_8_0]


def read_locationtable(cursor):
    cursor.execute("select LocationName, LocationId, RegionId from dbo.Location")
    result = cursor.fetchall()
    return {
        "LocationName": [i.LocationName for i in result],
        "LocationId": [i.LocationId for i in result],
        "RegionId": [i.RegionId for i in result],
    }


def does_location_exist(LocationTable, locationname, jurisdictionid):
    for i in range(len(LocationTable["LocationName"])):
        if (
            locationname == LocationTable["LocationName"][i]
            and jurisdictionid == LocationTable["RegionId"][i]
        ):
            return True
    return False


def get_location(LocationTable, locationname, jurisdictionid):
    for i in range(len(LocationTable["LocationName"])):
        if (
            locationname == LocationTable["LocationName"][i]
            and jurisdictionid == LocationTable["RegionId"][i]
        ):
            return LocationTable["LocationId"][i]
    return None


def validate_location(LocationTable, data, jurisdictionid):
    locationguid = uuid.uuid4()
    locationname = data["location name"]
    locationid = data["location id"] if "location id" in data else ""
    locationdesc = (
        data["location description"] if "location description" in data else ""
    )
    locationconfigxml = (
        '<?xml version="1.0"?>\n'
        '    <LocationConfig xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:xsd="http://www.w3.org/2001/XMLSchema">\n'
        "        <Approaches />\n"
        "        <MQTTCommEnabled>true</MQTTCommEnabled>\n"
        "    </LocationConfig>"
    )
    latitude = (
        float(data["latitude"])
        if "latitude" in data and data["latitude"] != ""
        else -360
    )
    longitude = (
        float(data["longitude"])
        if "longitude" in data and data["longitude"] != ""
        else -360
    )
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    parameters = {
        "RegionId": str(jurisdictionid),
        "LocationName": locationname,
        "LocationDescription": locationdesc,
        "Address": "",
        "City": "",
        "StateProvince": "",
        "PostalCode": "",
        "CreatedDateTime": now,
        "ModifiedDateTime": now,
        "CreatedUserId": 0,
        "ModifiedUserId": 0,
        "IsDeleted": 0,
        "IsActive": 1,
        "Latitude": latitude,
        "Longitude": longitude,
        "Elevation": 0,
        "LocationNumber": locationid,
        "LocationType": 1,
        "LocationConfigXml": locationconfigxml,
        "IsShared": 1,
        "AllianceId": str(uuid.UUID(int=0)),
        "ForeignId": str(uuid.UUID(int=0)),
        "ForeignRegionId": str(uuid.UUID(int=0)),
        "ControllerId": "",
    }

    LocationTable["LocationName"].append(locationname)
    LocationTable["LocationId"].append(locationguid)
    LocationTable["RegionId"].append(jurisdictionid)

    return parameters, locationguid


def commit_location_query(cursor, LocationTable, parameters, id):
    working_query_parameters = [
        id,
        parameters["LocationName"],
        parameters["LocationDescription"],
        parameters["Address"],
        parameters["City"],
        parameters["StateProvince"],
        parameters["PostalCode"],
        parameters["CreatedDateTime"],
        parameters["ModifiedDateTime"],
        parameters["CreatedUserId"],
        parameters["ModifiedUserId"],
        parameters["IsDeleted"],
        parameters["IsActive"],
        parameters["Latitude"],
        parameters["Longitude"],
        parameters["Elevation"],
        parameters["LocationNumber"],
        parameters["LocationType"],
        parameters["LocationConfigXml"],
        parameters["IsShared"],
        parameters["AllianceId"],
        parameters["ForeignId"],
        parameters["ForeignRegionId"],
    ]
    for version in CMS_VERSIONS:
        try:
            if version[0] == "6.10.0":
                query_parameters = working_query_parameters.copy()
                query_parameters.append(parameters["ControllerId"])
                query_parameters = tuple(query_parameters)
            elif version[0] == "6.8.0":
                query_parameters = working_query_parameters.copy()
                query_parameters = tuple(query_parameters)

            cursor.execute(
                f"{LOCATION_QUERY_TEMPLATE_MINIMAL}{version[1]}",
                query_parameters,
            )

            locationid = uuid.UUID(cursor.fetchval())

            logging.debug(
                f"Successfully commited Location to CMS Database version {version[0]}"
            )

            break
        except Exception:
            logging.warning(
                f"Failed to commit Location to CMS Database version {version[0]}"
            )

    LocationTable["LocationName"].append(parameters["LocationName"])
    LocationTable["LocationId"].append(locationid)
    LocationTable["RegionId"].append(id)

    return locationid
