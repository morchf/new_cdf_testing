import logging
import os
import boto3
from gtt.service.phase_selector import IntersectionService, PhaseSelectorService
from boto3.dynamodb.conditions import Key

logging.getLogger().setLevel(logging.INFO)

table_name = os.environ.get("INTERSECTIONS_TABLE_NAME")
instance_ids = os.environ.get("INSTANCE_IDS").split(",")
vps_table = os.environ.get("VPS_TABLE_NAME")
dynamo_table = boto3.resource("dynamodb").Table(table_name)
global_vps_table = boto3.resource("dynamodb").Table(vps_table)
ssm = boto3.client("ssm")
ec2 = boto3.client("ec2")

phase_selector_service = PhaseSelectorService(
    ssm, ec2, use_public_ip_addresses=os.environ.get("USE_PUBLIC_IPS") is not None
)
intersection_service = IntersectionService(dynamo_table, phase_selector_service)


def handler(event, context):
    for serial_number, ip_address, port in phase_selector_service.list_serial_numbers(
        instance_ids
    ):
        try:
            logging.info(
                f"Updating phase selector information with serial number - {serial_number}, ipaddress-{ip_address}, port-{port} "
            )
            query_results = global_vps_table.query(
                IndexName="vpsSearch",
                KeyConditionExpression=Key("VPS").eq(serial_number),
            )
            if query_results["Items"] and "agencyId" in query_results["Items"][0]:
                agency_id = query_results["Items"][0]["agencyId"].lower()
                if agency_id:
                    intersection_service.read(
                        agency_id=agency_id,
                        ip_address=ip_address,
                        port=port,
                    )
        except TimeoutError:
            logging.error(
                f"Timeout error for phase selector with serial number - {serial_number}, ipaddress-{ip_address}, port-{port}"
            )
            continue
        except Exception as e:
            logging.error(
                f"Exception for phase selector with serial number - {serial_number} - {e}"
            )
            continue
