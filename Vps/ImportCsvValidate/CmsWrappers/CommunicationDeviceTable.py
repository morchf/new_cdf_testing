import datetime
import uuid
import re

REGION_QUERY_TEMPLATE = """
DECLARE @Id uniqueidentifier;
EXEC [OpticomManagement].[dbo].[CommunicationDeviceInsert] @CommunicationDeviceTypeId=?,
                                                @LocationId=?,
                                                @CommunicationDeviceConfigurationXml=?,
                                                @CreatedDateTime=?,
                                                @ModifiedDateTime=?,
                                                @CreatedUserId=?,
                                                @ModifiedUserId=?,
                                                @IsDeleted=?,
                                                @IsActive=?,
                                                @Status=?,
                                                @StatusChangeDate=?,
                                                @VehicleId=?,
                                                @CommunicationDeviceId=@Id OUTPUT;
SELECT @Id as id;"""


def read_communicationdevicetable(cursor):
    cursor.execute(
        "select CommunicationDeviceId, DeviceName, LocationId "
        "from dbo.CommunicationDevice"
    )
    result = cursor.fetchall()
    return {
        "CommunicationDeviceId": [i.CommunicationDeviceId for i in result],
        "DeviceName": [i.DeviceName for i in result],
        "LocationId": [i.LocationId for i in result],
    }


def does_commdevice_exist(CommunicationDeviceTable, locationid):
    return locationid in CommunicationDeviceTable["LocationId"]


def get_commdevice(CommunicationDeviceTable, locationid):
    if does_commdevice_exist(CommunicationDeviceTable, locationid):
        return CommunicationDeviceTable["CommunicationDeviceId"][
            CommunicationDeviceTable["LocationId"].index(locationid)
        ]
    return None


def validate_commdevice(CommunicationDeviceTable, data, locationid, ipaddress, port):
    commdeviceid = uuid.uuid4()
    devicename = ipaddress + ": " + str(port)
    deviceaddress = data["device address"] if "device address" in data else "100000"
    if deviceaddress == "":
        deviceaddress = "100000"
    commdeviceconfigxml = (
        '<?xml version="1.0" encoding="utf-16"?>\n'
        '  <SocketLinkConfig xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:xsd="http://www.w3.org/2001/XMLSchema">\n'
        f"    <DeviceName>{devicename}</DeviceName>\n"
        f"    <DeviceAddress>{deviceaddress}</DeviceAddress>\n"
        f"    <IpAddr>{ipaddress}</IpAddr>\n"
        f"    <IpPort>{port}</IpPort>\n"
        "    <Protocol>Tcp</Protocol>\n"
        "  </SocketLinkConfig>"
    )
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    parameters = {
        "CommunicationDeviceTypeId": "0468E1B7-AB55-4be8-8042-7EF0DAB5F588",
        "LocationId": str(locationid),
        "CommunicationDeviceConfigurationXml": commdeviceconfigxml,
        "CreatedDateTime": now,
        "ModifiedDateTime": now,
        "CreatedUserId": 0,
        "ModifiedUserId": 0,
        "IsDeleted": 0,
        "IsActive": 1,
        "Status": 0,
        "StatusChangeDate": now,
        "VehicleId": str(uuid.UUID(int=0)),
    }

    CommunicationDeviceTable["DeviceName"].append(devicename)
    CommunicationDeviceTable["LocationId"].append(locationid)
    CommunicationDeviceTable["CommunicationDeviceId"].append(commdeviceid)

    return parameters, commdeviceid


def commit_commdevice_query(cursor, CommunicationDeviceTable, parameters, id):
    devicename = re.search(
        "(?<=<DeviceName>).*(?=</DeviceName>)",
        parameters["CommunicationDeviceConfigurationXml"],
    ).group(0)

    cursor.execute(
        REGION_QUERY_TEMPLATE,
        (
            uuid.UUID(str(parameters["CommunicationDeviceTypeId"])),
            uuid.UUID(str(id)),
            parameters["CommunicationDeviceConfigurationXml"],
            parameters["CreatedDateTime"],
            parameters["ModifiedDateTime"],
            parameters["CreatedUserId"],
            parameters["ModifiedUserId"],
            parameters["IsDeleted"],
            parameters["IsActive"],
            parameters["Status"],
            parameters["StatusChangeDate"],
            parameters["VehicleId"],
        ),
    )

    commdeviceid = uuid.UUID(cursor.fetchval())

    CommunicationDeviceTable["DeviceName"].append(devicename)
    CommunicationDeviceTable["LocationId"].append(id)
    CommunicationDeviceTable["CommunicationDeviceId"].append(commdeviceid)

    return commdeviceid


def add_commdevice(cursor, CommunicationDeviceTable, data, locationid, ipaddress, port):
    if not does_commdevice_exist(CommunicationDeviceTable, locationid):
        devicename = ipaddress + ": " + str(port)
        deviceaddress = data["device address"] if "device address" in data else "100000"
        if deviceaddress == "":
            deviceaddress = "100000"
        commdeviceconfigxml = (
            '<?xml version="1.0" encoding="utf-16"?>\n'
            '  <SocketLinkConfig xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema">\n'
            f"    <DeviceName>{devicename}</DeviceName>\n"
            f"    <DeviceAddress>{deviceaddress}</DeviceAddress>\n"
            f"    <IpAddr>{ipaddress}</IpAddr>\n"
            f"    <IpPort>{port}</IpPort>\n"
            "    <Protocol>Tcp</Protocol>\n"
            "  </SocketLinkConfig>"
        )
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        parameters = (
            "0468E1B7-AB55-4be8-8042-7EF0DAB5F588",
            locationid,
            commdeviceconfigxml,
            now,
            now,
            0,
            0,
            0,
            1,
            0,
            now,
            uuid.UUID(int=0),
        )

        cursor.execute(REGION_QUERY_TEMPLATE, parameters)

        commdeviceid = cursor.fetchval()

        CommunicationDeviceTable["DeviceName"].append(devicename)
        CommunicationDeviceTable["LocationId"].append(locationid)
        CommunicationDeviceTable["CommunicationDeviceId"].append(commdeviceid)

        return "Created", commdeviceid
    else:
        return get_commdevice(CommunicationDeviceTable, locationid)
