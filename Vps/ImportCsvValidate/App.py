import pyodbc
import re
import json
import os
import boto3
import base64
from CmsWrappers import RegionTable, LocationTable, CommunicationDeviceTable
from uuid import UUID
import logging

logging.basicConfig(level=logging.DEBUG)


class UUIDEncoder(json.JSONEncoder):
    # UUID encoder for the jsondupms
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)


CMS_DATABASE_NAME = "OpticomManagement"
codeBldTab = os.environ["CodeDeployTable"]
glbMcTab = os.environ["VpsTable"]
stepFun = os.environ["ImportUtilityStepFunctionArn"]

dyanmoTable = boto3.resource("dynamodb", region_name="us-east-1")
stepFunClnt = boto3.client("stepfunctions", "us-east-1")


def read_csv(event):
    """Reads in a base64 encoded csv from the input to the lambda function

    Arguments:
        event {dict} -- a python dictionary with the attribute "body"

    Returns:
        dict -- A dictionary with columns as keys and rows as values
    """
    file = base64.b64decode(event["body"])
    decoded_data = [i.split(",") for i in file.decode("utf-8").splitlines()]
    data = {}
    for i in range(len(decoded_data[0])):
        data[decoded_data[0][i].lower()] = [
            decoded_data[j][i] for j in range(1, len(decoded_data))
        ]
    return data


# Verify Input Information
def check_string(s, max_length, ok_empty=True):
    return type(s) == str and len(s) < max_length and (not s == "" or ok_empty)


def check_int(i, low, high, ok_empty=True):
    if i == "" and ok_empty:
        return True
    try:
        i = int(i)
        return low <= i <= high
    except Exception:
        return False


def check_double(d, low, high, ok_empty=True):
    if d == "" and ok_empty:
        return True
    try:
        d = float(d)
        return low <= d <= high
    except Exception:
        return False


def check_comm_type(s, ok_empty=True):
    if s == "" and ok_empty:
        return True
    return (
        False
        if s.lower() not in ["serial", "tcp/ip", "centralized", "offline"]
        else True
    )


def extract_ip_address(ip):
    match = re.search(
        "^(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\\."
        "(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\\."
        "(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\\."
        "(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$",
        ip.strip(),
    )
    return match.group() if match is not None else match


def validate_input(data):
    """Validates the input data. Checks for all columns having the same number of rows,
    required columns, data types and duplicate values in specific columns

    Arguments:
        data {dict{'column1': list}} -- data in a columnar dict format

    Raises:
        ValueError: Not all lines have the same number of columns
        ValueError: Required Columns are missing
        ValueError: Data is of the wrong type or outside the bounds of what is allowed
        ValueError: Duplicate Values found in specific columns
        ValueError: Jurisdiction Name does not contain all the same values
    """
    # All rows must have the same length
    if not all([len(data[i]) == len(data["jurisdiction name"]) for i in data]):
        raise ValueError(
            "Corrupted CSV.  All lines must have the same number of columns"
        )

    # Must have these columns
    for colName in [
        "jurisdiction name",
        "location name",
        "location id",
        "latitude",
        "longitude",
        "comm device type",
    ]:
        if not data.get(colName, False):
            raise ValueError(f'Missing required column "{colName}"')

    # Check values in the input
    if not all([check_string(i, 200, False) for i in data.get("jurisdiction name")]):
        raise ValueError(
            "Unable to parse input data.  Invalid data or data type for "
            'column "jurisdiction name"'
        )

    if not all([check_string(i, 255, False) for i in data.get("location name")]):
        raise ValueError(
            "Unable to parse input data.  Invalid data or data type for "
            'column "location name"'
        )

    if not (
        all([check_string(i, 600, True) for i in data.get("jurisdiction desc")])
        if data.get("jurisdiction desc", None) is not None
        else True
    ):
        raise ValueError(
            "Unable to parse input data.  Invalid data or data type for "
            'column "jurisdiction desc"'
        )

    if not all([check_string(i, 50, False) for i in data.get("location id")]):
        raise ValueError(
            "Unable to parse input data.  Invalid data or data type for "
            'column "location id"'
        )

    if not (
        all([check_string(i, 200, True) for i in data.get("location desc")])
        if data.get("location desc", None) is not None
        else True
    ):
        raise ValueError(
            "Unable to parse input data.  Invalid data or data type for "
            'column "location desc"'
        )

    if not all([check_comm_type(i, False) for i in data.get("comm device type")]):
        raise ValueError(
            "Unable to parse input data.  Invalid data or data type for "
            'column "comm device type"'
        )

    if not (
        all([check_int(i, 0, 99999, True) for i in data.get("device address")])
        if data.get("device address", None) is not None
        else True
    ):
        raise ValueError(
            "Unable to parse input data.  Invalid data or data type for "
            'column "device address"'
        )

    if not all(
        [check_double(i, -89.999999, 89.999999, False) for i in data.get("latitude")]
    ):
        raise ValueError(
            "Unable to parse input data.  Invalid data or data type for "
            'column "latitude"'
        )

    if not all(
        [check_double(i, -179.999999, 179.999999, False) for i in data.get("longitude")]
    ):
        raise ValueError(
            "Unable to parse input data.  Invalid data or data type for "
            'column "longitude"'
        )

    # Check for duplicates in specific columns
    for colName in ["location name", "location id"]:
        if len(data[colName]) != len(set(data[colName])):
            raise ValueError(f'Found duplicate data in column "{colName}"')

    # Must all be the same Value
    if len(set(data["jurisdiction name"])) != 1:
        raise ValueError('Column "jurisdiction name" does not contain constant values')

    # Convert data to row based format
    items = []
    for row in range(len(data["location name"])):
        item = {}
        for column in data:
            item[column] = data[column][row]
        items.append(item)

    return items


def get_cms_credentials(customerName):
    """Takes the customerName and retrieves the CMS username, password and
    ip address from AWS Secrets Manager

    Arguments:
        customerName {String} -- The name of the customer to retrieve details for

    Returns:
        String -- username for the CMS database
        String -- password for the CMS database
        String -- ip address for the CMS database
    """
    cms_credentials = json.loads(
        boto3.client("secretsmanager").get_secret_value(SecretId=customerName)[
            "SecretString"
        ]
    )
    return (
        cms_credentials["username"],
        cms_credentials["password"],
        cms_credentials["host"],
    )


def connect_to_cms(uid, pwd, ip):
    """Tries to connect to the CMS database

    Arguments:
        uid {String} -- username for the CMS database
        pwd {String} -- password for the CMS database
        ip {String} -- ip address of the CMS database

    Returns:
        Pyodbc Connection -- The connection for the CMS database
        Pyodbc Cursor -- The cursor for the CMS database
    """
    try:
        cnxn = pyodbc.connect(
            "DRIVER={};SERVER={};DATABASE={};UID={};PWD={}".format(
                "{ODBC Driver 17 for SQL Server}", ip, CMS_DATABASE_NAME, uid, pwd
            ),
            timeout=7,
        )
        cursor = cnxn.cursor()
        cursor.execute("select '1'")
        cursor.close()
        return cnxn, cnxn.cursor()
    except Exception as e:
        logging.debug(e)


def nextAvailable(available):
    """Returns the next properly-formatted VPS from the given list, and raises
    an exception if no proper VPSs are available

    Arguments:
        available {list} -- List of dictionary, each dictionary contains the
                             details for a single VPS

    Raises:
        ValueError: No VPS is available

    Returns:
        int -- Primary Key of the VPS
        String -- VPS serial number
        String -- VPS Ip Address
        int -- Port Number
    """
    next = available.pop(0)

    try:
        PrimaryKey = next["primaryKey"]
        VPS = next["VPS"]
        IpAddress = extract_ip_address(next["dockerIP"])
        PortNumber = next["dockerPort"]
    except Exception:
        return nextAvailable(available)

    if IpAddress is None or not check_int(PortNumber, 1, 65535, False):
        return nextAvailable(available)

    return PrimaryKey, VPS, IpAddress, PortNumber


def get_all_available_vps(customerName):
    """Reads ALL available VPS's for the customer (customerName) from
    the "VpsTable" DynamoDb table

    Arguments:
        customerName {String} -- The customer name

    Returns:
        list -- A list of dictionaries with each dictionary being a single VPS
    """
    vpstable = dyanmoTable.Table(glbMcTab)
    response = vpstable.query(
        IndexName="vpsAvailabilityGSI",
        KeyConditionExpression="customerName = :customerName AND "
        "vpsAvailability = :vpsavailability",
        ExpressionAttributeValues={
            ":customerName": customerName,
            ":vpsavailability": "AVAILABLE",
            ":dockerStatus": "running",
        },
        FilterExpression="dockerStatus = :dockerStatus",
    )
    available = response["Items"]
    while "LastEvaluatedKey" in response:
        response = vpstable.query(
            IndexName="vpsAvailabilityGSI",
            KeyConditionExpression="customerName = :customerName AND "
            "vpsAvailability = :vpsavailability",
            ExpressionAttributeValues={
                ":customerName": customerName,
                ":vpsavailability": "AVAILABLE",
                ":dockerStatus": "running",
            },
            ExclusiveStartKey=response["LastEvalutaedKey"],
            FilterExpression="dockerStatus = :dockerStatus",
        )
        available.extend(response["Items"])

    return available


def configure_intersection_transaction(
    available,
    data,
    regiontable,
    locationtable,
    communicationdevicetable,
):
    customer = data["jurisdiction name"]
    operations = []

    # Add new jurisdiction or get preexisting jurisdiction
    jurisdictionid = RegionTable.get_region(regiontable, data["jurisdiction name"])
    if jurisdictionid is None:
        parameters, jurisdictionid = RegionTable.validate_region(regiontable, data)
        operations.append({"Type": "REGION", "Parameters": parameters})

    # Add new location or get preexisting location
    locationid = LocationTable.get_location(
        locationtable, data["location name"], jurisdictionid
    )
    if locationid is None:
        parameters, locationid = LocationTable.validate_location(
            locationtable, data, jurisdictionid
        )
        operations.append(
            {"Type": "LOCATION", "Parameters": parameters, "RegionName": customer}
        )

    # Add new commdevice
    commdeviceid = CommunicationDeviceTable.get_commdevice(
        communicationdevicetable, locationid
    )
    if commdeviceid is None:
        PrimaryKey, VPS, IpAddress, PortNumber = nextAvailable(available)
        operations.append(
            {
                "Type": "VPS",
                "primaryKey": int(PrimaryKey),
                "VPS": VPS,
                "IpAddress": IpAddress,
                "PortNumber": int(PortNumber),
            }
        )
        parameters, commdeviceid = CommunicationDeviceTable.validate_commdevice(
            communicationdevicetable, data, locationid, IpAddress, PortNumber
        )
        operations.append(
            {
                "Type": "COMMDEVICE",
                "Parameters": parameters,
                "LocationName": data["location name"],
            }
        )

    return operations


def write_dynamodb_payload(customerName, payload):
    """Write lambda output to DynamoDb

    Arguments:
        customerName {String} -- The customer's name
        payload {String} -- A json string output for writing to CMS
    """
    dyanmoTable.Table(codeBldTab).update_item(
        Key={"customerName": customerName},
        UpdateExpression="set sqlSerial = :payload",
        ExpressionAttributeValues={":payload": payload},
    )


def commit_import_in_progress(customerName):
    dyanmoTable.Table(codeBldTab).update_item(
        Key={"customerName": customerName},
        UpdateExpression="set importInProgress = :importInProgressVal",
        ExpressionAttributeValues={":importInProgressVal": True},
    )


def rollback_import_in_progress(customerName):
    """Rollback the output in dynamodb if something fails after writing to dynamodb

    Arguments:
        customerName {String} -- The customer's name
    """
    dyanmoTable.Table(codeBldTab).update_item(
        Key={"customerName": customerName},
        UpdateExpression="set importInProgress = :importInProgressVal",
        ExpressionAttributeValues={":importInProgressVal": False},
    )


def call_commit_function(customerName):
    """Start the Step Function with the customerName as input

    Arguments:
        customerName {String} -- The customer's name
    """
    boto3.client("stepfunctions").start_execution(
        stateMachineArn=os.environ["ImportUtilityStepFunctionArn"],
        input=json.dumps({"customerName": customerName}),
    )


def lambda_handler(event, context):
    # Read the Data, Validate it and Validate that
    #  there are enough available VPSs to configure
    try:
        data = read_csv(event)
        data = validate_input(data)
        customerName = data[0]["jurisdiction name"]
        logging.debug("customer name: %s", customerName)
    except Exception as e:
        logging.debug(e)
        retMessage = {
            "errorNumber": 401,
            "errorMessage": f"Incorrectly formatted data: {str(e)}.",
        }
        return {
            "statusCode": 400,
            "body": json.dumps(retMessage),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }

    try:
        commit_import_in_progress(customerName)
    except Exception:
        retMessage = {
            "errorNumber": 501,
            "errorMessage": "Failed to update DynamoDB Table",
        }
        return {
            "statusCode": 500,
            "body": json.dumps(retMessage),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }

    # Retrieve CMS Database Credentials for the Given customer
    try:
        uid, pwd, ip = get_cms_credentials(customerName)
    except Exception as e:
        logging.debug(e)
        rollback_import_in_progress(customerName)
        retMessage = {
            "errorNumber": 502,
            "errorMessage": "Unable to access cms credentials for "
            '"customer "{customerName}"',
        }
        return {
            "statusCode": 500,
            "body": json.dumps(retMessage),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }

    # Connect to CMS Database
    try:
        cnxn, cursor = connect_to_cms(uid, pwd, ip)
    except Exception as e:
        logging.debug(e)
        rollback_import_in_progress(customerName)
        retMessage = {
            "errorNumber": 503,
            "errorMessage": "Unable to connect to cms database",
        }
        return {
            "statusCode": 500,
            "body": json.dumps(retMessage),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }

    # Read required data from the CMS database
    try:
        regiontable = RegionTable.read_regiontable(cursor)
        locationtable = LocationTable.read_locationtable(cursor)
        communicationdevicetable = (
            CommunicationDeviceTable.read_communicationdevicetable(cursor)  # noqa: E501
        )
    except Exception as e:
        logging.debug(e)
        rollback_import_in_progress(customerName)
        retMessage = {
            "errorNumber": 504,
            "errorMessage": "Unable to read system database",
        }
        return {
            "statusCode": 500,
            "body": json.dumps(retMessage),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }

    # Read all available VPSs
    try:
        available = get_all_available_vps(customerName)
    except Exception as e:
        logging.debug(e)
        rollback_import_in_progress(customerName)
        retMessage = {
            "errorNumber": 505,
            "errorMessage": "Unable to read system database",
        }
        return {
            "statusCode": 500,
            "body": json.dumps(retMessage),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }

    # Process the records row by row
    try:
        locationsToCommit = []
        for row in data:
            if (
                row["location name"]
                and row["location name"].lower() != "RouteEnd".lower()
            ):
                result = configure_intersection_transaction(
                    available,
                    row,
                    regiontable,
                    locationtable,
                    communicationdevicetable,
                )

                if len(result) > 0:
                    locationsToCommit.append(result)
    except Exception as e:
        logging.debug(e)
        rollback_import_in_progress(customerName)
        retMessage = {
            "errorNumber": 506,
            "errorMessage": "Not enough available VPSs to configure "
            "requested intersections",
        }
        return {"statusCode": 500, "body": json.dumps(retMessage)}

    if len(locationsToCommit) > 0:
        try:
            write_dynamodb_payload(
                customerName, json.dumps(locationsToCommit, cls=UUIDEncoder)
            )
        except Exception as e:
            logging.debug(e)
            rollback_import_in_progress(customerName)
            retMessage = {
                "errorNumber": 402,
                "errorMessage": "Another import job is already in progress"
                f"for customer {customerName}, please try again later",
            }
            return {
                "statusCode": 400,
                "body": json.dumps(retMessage),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }

    try:
        stepFunClnt.start_execution(
            stateMachineArn=stepFun,
            input='{"customerName": "%s"}' % (customerName),
        )
    except Exception as e:
        rollback_import_in_progress(customerName)
        logging.debug(e)
        retMessage = {
            "errorNumber": 507,
            "errorMessage": "Failed to invoke the step function",
        }
        return {
            "statusCode": 500,
            "body": json.dumps(retMessage),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }

    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": "Import process initiated",
    }
