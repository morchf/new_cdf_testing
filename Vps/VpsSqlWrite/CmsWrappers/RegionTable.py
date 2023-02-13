import uuid


REGION_QUERY_TEMPLATE = """
                DECLARE @Id uniqueidentifier;
                EXEC [OpticomManagement].[dbo].[RegionInsert] @Name=?,
                                                              @Description=?,
                                                              @SecurityLevel=?,
                                                              @IsDeleted=?,
                                                              @RegionConfigXml=?,
                                                              @IsShared=?,
                                                              @AllianceId=?,
                                                              @ForeignId=?,
                                                              @RegionId=@Id OUTPUT;
                SELECT @Id as id;"""


def read_regiontable(cursor):
    cursor.execute("select Name, RegionId from dbo.Region")
    result = cursor.fetchall()
    return {"Name": [i.Name for i in result], "RegionId": [i.RegionId for i in result]}


def does_region_exist(RegionTable, name):
    return name in RegionTable["Name"]


def get_region(RegionTable, name):
    if does_region_exist(RegionTable, name):
        return RegionTable["RegionId"][RegionTable["Name"].index(name)]
    return None


def validate_region(RegionTable, data):
    name = data["jurisdiction name"]
    jurisdictionid = uuid.uuid4()
    description = (
        data.get("jurisdiction description", "")
        if "jurisdiction description" in data
        else ""
    )
    regionconfigxml = (
        '<?xml versi`on="1.0"?>\n'
        '    <RegionConfig xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:xsd="http://www.w3.org/2001/XMLSchema">\n'
        "        <CentralizedDistribution>\n"
        "        <Protocol>0</Protocol>\n"
        "        <Address>192.168.0.1</Address>\n"
        "        <Port>7700</Port>\n"
        "        <Version>1</Version>\n"
        "        </CentralizedDistribution>\n"
        "    </RegionConfig>"
    )

    parameters = {
        "Name": name,
        "Description": description,
        "SecurityLevel": 0,
        "IsDeleted": 0,
        "RegionConfigXml": regionconfigxml,
        "IsShared": 1,
        "AllianceId": uuid.UUID(int=0),
        "ForeignId": uuid.UUID(int=0),
    }

    RegionTable["RegionId"].append(jurisdictionid)
    RegionTable["Name"].append(name)

    return parameters, jurisdictionid


def commit_region_query(cursor, RegionTable, parameters):
    cursor.execute(
        REGION_QUERY_TEMPLATE,
        (
            parameters["Name"],
            parameters["Description"],
            parameters["SecurityLevel"],
            parameters["IsDeleted"],
            parameters["RegionConfigXml"],
            parameters["IsShared"],
            uuid.UUID(str(parameters["AllianceId"])),
            uuid.UUID(str(parameters["ForeignId"])),
        ),
    )

    jurisdictionid = uuid.UUID(cursor.fetchval())

    RegionTable["RegionId"].append(jurisdictionid)
    RegionTable["Name"].append(parameters["Name"])

    return jurisdictionid


def add_region(cursor, RegionTable, data):
    name = data["jurisdiction name"]
    if not does_region_exist(RegionTable, name):
        description = (
            data.get("jurisdiction description", "")
            if "jurisdiction description" in data
            else ""
        )
        regionconfigxml = (
            '<?xml versi`on="1.0"?>\n'
            '    <RegionConfig xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema">\n'
            "        <CentralizedDistribution>\n"
            "        <Protocol>0</Protocol>\n"
            "        <Address>192.168.0.1</Address>\n"
            "        <Port>7700</Port>\n"
            "        <Version>1</Version>\n"
            "        </CentralizedDistribution>\n"
            "    </RegionConfig>"
        )

        parameters = (
            name,
            description,
            0,
            0,
            regionconfigxml,
            1,
            str(uuid.UUID(int=0)),
            str(uuid.UUID(int=0)),
        )

        cursor.execute(REGION_QUERY_TEMPLATE, parameters)

        jurisdictionid = cursor.fetchval()

        RegionTable["RegionId"].append(jurisdictionid)
        RegionTable["Name"].append(name)

        return "Created", jurisdictionid
    else:
        idx = RegionTable["Name"].index(name)
        return "Preexisting", RegionTable["RegionId"][idx]
