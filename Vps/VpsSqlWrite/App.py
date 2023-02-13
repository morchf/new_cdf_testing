import os
import boto3
import json
import pyodbc
from decimal import Decimal
from CmsWrappers import RegionTable, LocationTable, CommunicationDeviceTable
import logging

logging.basicConfig(level=logging.DEBUG)

CMS_DATABASE_NAME = "OpticomManagement"
vpsTbl = boto3.resource("dynamodb", region_name="us-east-1").Table(
    os.environ["VpsTable"]
)
codeBldTbl = boto3.resource("dynamodb", region_name="us-east-1").Table(
    os.environ["CodeDeployTable"]
)


def rollback_import_in_progress(customerName):
    """Rollback the output in dynamodb if something fails after writing to dynamodb

    Arguments:
        customerName {String} -- The customer's name
    """
    codeBldTbl.update_item(
        Key={"customerName": customerName},
        UpdateExpression="set importInProgress = :importInProgressVal",
        ExpressionAttributeValues={":importInProgressVal": False},
    )


def get_cms_credentials(customerName):
    """Retrieves the customer's cms credentials from aws Secrets Manager

    Arguments:
        customerName {String} -- The customer's name

    Returns:
        String -- The CMS username
        String -- The CMS password
        String -- The CMS ip address
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
    """Connects to CMS given the Username, Password and ip address

    Arguments:
        uid {String} -- Username for the CMS database
        pwd {String} -- Password for the CMS database
        ip {String} -- Ip address of the CMS database

    Returns:
        Pyodbc connection -- A connection to the CMS database
        Pyodbc cursor -- A cursor for the CMS database
    """
    cnxn = pyodbc.connect(
        "DRIVER={};SERVER={};DATABASE={};UID={};PWD={}".format(
            "{ODBC Driver 17 for SQL Server}", ip, CMS_DATABASE_NAME, uid, pwd
        )
    )
    return cnxn, cnxn.cursor()


def mark_vps_in_use(operation):
    """Updates a VPS in the VPS table in DynamoDB from AVAILABLE to INUSE

    Arguments:
        operation {list} -- A set of operations for SQL that represent a
        single transaction for an intersection
    """
    vpsTbl.update_item(
        Key={"primaryKey": operation["primaryKey"]},
        UpdateExpression="set vpsAvailability = :newStatus",
        ExpressionAttributeValues={":oldStatus": "AVAILABLE", ":newStatus": "INUSE"},
        ConditionExpression="vpsAvailability = :oldStatus",
    )


def read_payload(customerName):
    # Read Json String from DynamoDB
    response = codeBldTbl.get_item(Key={"customerName": customerName},)
    return json.loads(response["Item"]["sqlSerial"])


def lambda_handler(event, context):
    # Setup required input data and constants
    customerName = event["customerName"]

    # Read Input Data
    try:
        data = read_payload(customerName)
    except Exception as e:
        logging.debug(e)
        rollback_import_in_progress(customerName)
        raise e

    # Retrieve CMS Database Credentials for the Given customer
    try:
        uid, pwd, ip = get_cms_credentials(customerName)
    except Exception as e:
        logging.debug(e)
        rollback_import_in_progress(customerName)
        raise ValueError(
            "Unable to access credentials for cms database for"
            f' customer "{customerName}"'
        )

    # Connect to CMS Database
    try:
        cnxn, cursor = connect_to_cms(uid, pwd, ip)
    except Exception as e:
        rollback_import_in_progress(customerName)
        logging.debug(e)
        raise ConnectionError(
            f'Unable to connect to cms database for customer "{customerName}"'
        )

    # Read required data from the CMS database
    try:
        regiontable = RegionTable.read_regiontable(cursor)
        locationtable = LocationTable.read_locationtable(cursor)
        communicationdevicetable = CommunicationDeviceTable.read_communicationdevicetable(  # noqa: 501
            cursor
        )
    except Exception as e:
        logging.debug(e)
        rollback_import_in_progress(customerName)
        raise IOError(f'Unable to read system database for customer "{customerName}"')

    locationsToConfigure = []
    try:
        for transaction in data:
            tempAppend = {}
            for operation in transaction:
                if operation["Type"] == "VPS":
                    tempAppend["deviceName"] = operation["VPS"]
                    tempAppend["primaryKey"] = operation["primaryKey"]
                    mark_vps_in_use(operation)
                elif operation["Type"] == "REGION":
                    regionid = RegionTable.commit_region_query(
                        cursor, regiontable, operation["Parameters"]
                    )
                elif operation["Type"] == "LOCATION":
                    regionid = RegionTable.get_region(
                        regiontable, operation["RegionName"]
                    )
                    if regionid is None:
                        logging.error("REGION ID FAILED")
                        raise ValueError(
                            "Internal Error: Expected RegionId for Region "
                            f"\"{operation['RegionName']}\" but Region does not exist"
                        )
                    tempAppend["latitude"] = Decimal(
                        "{:.6f}".format(float(operation["Parameters"]["Latitude"]))
                    )
                    tempAppend["longitude"] = Decimal(
                        "{:.6f}".format(float(operation["Parameters"]["Longitude"]))
                    )
                    tempAppend["intersectionName"] = operation["Parameters"][
                        "LocationName"
                    ]
                    locationid = LocationTable.commit_location_query(
                        cursor, locationtable, operation["Parameters"], regionid
                    )
                elif operation["Type"] == "COMMDEVICE":
                    locationid = LocationTable.get_location(
                        locationtable, operation["LocationName"], regionid
                    )
                    if locationid is None:
                        raise ValueError(
                            "Internal Error: Expected LocationId for Location "
                            f"\"{operation['LocationName']}\" but Location does "
                            "not exist"
                        )
                    CommunicationDeviceTable.commit_commdevice_query(
                        cursor,
                        communicationdevicetable,
                        operation["Parameters"],
                        locationid,
                    )
            locationsToConfigure.append(tempAppend)
        cnxn.commit()
    except Exception as e:
        logging.debug(e)
        cnxn.rollback()
        rollback_import_in_progress(customerName)
        raise e

    # If we have added new intersections, update the item in dynamoDB
    if len(locationsToConfigure) > 0:
        codeBldTbl.update_item(
            Key={"customerName": customerName},
            UpdateExpression="set vpsSerial = :toConfig",
            ExpressionAttributeValues={":toConfig": locationsToConfigure},
        )
    else:
        rollback_import_in_progress(customerName)

    return {"customerName": customerName}
