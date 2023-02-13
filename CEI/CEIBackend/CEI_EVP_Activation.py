import boto3
import time
import sys, os
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
import logging
from CEI_Logging import post_log


dynamodb = boto3.resource("dynamodb")
iot_client = boto3.client("iot-data")


def activate_vehicle(site_id, agency_id, device_id, vehicle_id, CAD_msg_id, activate):
    """Primary vehicle control function

    Args:
        siteId (uuid): Region Identifier - used in topic, msgIdx determination
        vehicleSN (string): Vehicle Identifier - used in topic construction
        activate (bool): Enable/Disable probe - used in priority control

    Returns:
        string: IoT Publish result
    """

    """
        Reserve msgIdx - Five attempts before failing
        """
    msg_log_posted = False
    attempts = 0
    idx = 1
    while not msg_log_posted and attempts < 5:
        idx = get_msg_idx(site_id)

        if not isinstance(idx, int):
            post_log(
                site_id,
                agency_id,
                device_id,
                CAD_msg_id,
                "Error",
                "Message Index Acquisition",
                "CEI EVP Activation",
                idx,
            )
            break
        logging.info(f"IDX found - {idx} ")
        post_msg_results = post_msg_log(site_id, idx)

        logging.info(f"Post results - {post_msg_results} ")

        if "Error" in post_msg_results:
            attempts += 1
        else:
            logging.info("Idx Reserved")
            msg_log_posted = True

    if not msg_log_posted:
        logging.info("Count not post msgLog")
        post_log(
            site_id,
            agency_id,
            device_id,
            CAD_msg_id,
            "Error",
            "Message Index Processing",
            "CEI EVP Activation",
            post_msg_results,
        )
        return idx

    """
        Construct Data Packet
        """
    command_id = 49
    message_id = idx.to_bytes(4, byteorder="big")
    msgData = 0 if activate else 1
    checksum = (
        command_id
        + message_id[0]
        + message_id[1]
        + message_id[2]
        + message_id[3]
        + msgData
    ).to_bytes(2, byteorder="big")
    messageArray = [
        command_id,
        message_id[0],
        message_id[1],
        message_id[2],
        message_id[3],
        0,
        0,
        0,
        0,
        msgData,
        checksum[0],
        checksum[1],
    ]

    """
        Construct IoT Topic, publish
        """
    response = iot_client.publish(
        topic=f"GTT/{site_id}/SVR/EVP/2100/{vehicle_id}/STATE",
        qos=0,
        payload=bytearray(messageArray),
    )
    post_log(
        site_id,
        agency_id,
        device_id,
        CAD_msg_id,
        "Info",
        "IoT Message Processing",
        "CEI EVP Activation",
        response,
    )
    return response


def get_msg_idx(site_id):
    """Get the current message index for the site

    Args:
        siteId (uuid): id of site being referenced

    Returns:
        (integer): index of curret site message
    """
    idx = 1
    # Get msgIdx - if new Site, create new entry
    table = dynamodb.Table("cei-iot-msg-idx")
    response = table.query(KeyConditionExpression=Key("siteId").eq(site_id))
    if response.get("Count", 0) == 0:
        try:
            entry = {"siteId": site_id, "idx": idx}
            table.put_item(Item=entry)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(
                f"400 Error - MsgIdx Processing failed (put) {e} {exc_type} {fname} {exc_tb.tb_lineno}... "
            )
            return f"400 Error - MsgIdx Processing failed (put) {e} {exc_type} {fname} {exc_tb.tb_lineno}... "

    else:
        logging.info(response.get("Items", None)[0])
        idx = response.get("Items", None)[0].get("idx", "derp") + 1
        logging.info(f"MsgIdx found {idx}")

    return int(idx)


def post_msg_log(site_id, idx):
    """
    Update site idx in DynamoDB
    Args:
        siteId (uuid): ID for Installation being updated
        idx (integer): message indexc being updated to

    Returns:
        response (string): dynamo operation result
    """
    logging.info("Posting message log...")
    msg_log = {
        "msgId": f"{site_id}_{idx}",
        "timestamp": int(time.time()),
        "responseCode": "TDB",
        "lifeSpan": int(time.time()) + 1200,
    }
    try:
        table = dynamodb.Table("cei-iot-msg-log")
        response = table.put_item(
            Item=msg_log, ConditionExpression="attribute_not_exists(msgId)"
        )

        update_idx_table(site_id, idx)

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            response = f"Error - MsgIdx reempted - retrying... ({e})"
            logging.error(response)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        response = f"400 Error - MsgIdx Processing failed (put) {e} {exc_type} {fname} {exc_tb.tb_lineno}..."
        logging.error(response)

    return response


def update_idx_table(site_id, idx):
    """Update dynamoDB table

    Args:
        siteId (uuid): Region to update the idx for
        idx (integer): value of new IDX

    Returns:
        (string): results of operations
    """
    table = dynamodb.Table("cei-iot-msg-idx")
    response = table.update_item(
        Key={
            "siteId": site_id,
        },
        UpdateExpression="SET idx = :val0",
        ExpressionAttributeValues={":val0": idx},
        ReturnValues="UPDATED_NEW",
    )
    return response
