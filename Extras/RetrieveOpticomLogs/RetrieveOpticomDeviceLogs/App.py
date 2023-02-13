import json
import boto3
import pyodbc
import os
import logging
import csv
import io

logging.basicConfig(level=logging.DEBUG)


def get_cms_credentials(customerName):
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
    cnxn = pyodbc.connect(
        "DRIVER={};SERVER={};DATABASE={};UID={};PWD={}".format(
            "{ODBC Driver 17 for SQL Server}", ip, "OpticomManagement", uid, pwd
        )
    )
    return cnxn, cnxn.cursor()


def lambda_handler(event, context):
    customerName = event["customerName"]
    locationNames = event["locationNames"].split(",")
    locationNames = ", ".join([f"'{i.strip()}'" for i in locationNames])
    startTime = event["timeFrom"]
    endTime = event["timeTo"]

    uid, pwd, ip = get_cms_credentials(customerName)
    cnxn, cursor = connect_to_cms(uid, pwd, ip)
    cursor.execute(
        "SELECT * FROM [OpticomManagement].[dbo].[OpticomDeviceLog] WHERE"
        f" LocationName IN ({locationNames}) AND StartDateTime > "
        f"CONVERT(datetime, '{startTime}') AND StartDateTime < "
        f"CONVERT(datetime, '{endTime}')"
    )

    columns = [column[0].lower() for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for row in results:
        writer.writerow(row)
    filestring = output.getvalue()

    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=os.environ["S3Bucket"],
        Key="OpticomLogsData/Results.csv",
        Body=filestring.encode("utf-8"),
    )
