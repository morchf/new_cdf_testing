# flake8: noqa
# fmt: off
import json
import uuid
import time
import boto3
import logging
import os

from CEI_Dynamo_Cache import get_agency_name


client = boto3.client("firehose")
streamname = "CEI-logStream"

def post_log(
    site_id,
    agency_id,
    device_CEI_id,
    CAD_message_id,
    category,
    subtype,
    source,
    message,
):
    """log action - push log to S3 Via Kinesis Firehose

    Args:
        siteId (uuid): Id of site/installation source of message
        siteName (string): name of site/installation source of message
        agencyId (uuid): id of agency source of message
        deviceCEIID (uuid): deviceId of the device in question
        CADmessageId (uuid): id of message from CAD
        category (string): broad type of the log being passed
        subtype (string): specific type of the log beind passed
        source (string): process/code source of the message
        message (string): log details being recorded.
    """
    try:
        log_data = []
        agencyName = "None"
        try:
            agencyName = get_agency_name(site_id, agency_id)
        except:
            pass

        log = {
            "logid": str(uuid.uuid4()),
            "timestamp": str(time.time()),
            "siteid": str(site_id),
            "agencyid": str(agency_id),
            "agencyname": agencyName,
            "deviceid": device_CEI_id,
            "deviceceiid": str(device_CEI_id),
            "cadmessageid": str(CAD_message_id),
            "category": str(category),
            "subtype": str(subtype),
            "source": str(source),
            "message": str(message).replace("|||", '"'),
        }
        logging.info(f"Log Data - {log}")
        log_data.append({"Data": json.dumps(log).encode()})
        result = client.put_record_batch(
            DeliveryStreamName=streamname, Records=log_data
        )
        result = f"Log Result = {result}"
        logging.info(result)
        return result
    except Exception as e:
        result = f"Error - {e}"
        logging.error(result)
        return result
