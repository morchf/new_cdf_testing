# flake8: noqa
# fmt: off
import json
import boto3
from botocore.awsrequest import AWSRequest
from botocore.endpoint import URLLib3Session
from botocore.auth import SigV4Auth
import time
from CEI_EVP_Activation import activate_vehicle
import os
import logging
from CEI_Logging import post_log

from CEI_Dynamo_Cache import get_vehicle
from CEI_Dynamo_Cache import get_all_agencies
from CEI_Dynamo_Cache import get_agency_assets
from CEI_Dynamo_Cache import get_gtt_serial
from CEI_Dynamo_Cache import record_entry

#Depricated August 23, 2021

def EVPTimeout(event, context):
    """System Wide Timeout processing
    - run through each agency and check for last referenced on each vehicle

    Args:
            event (dictionary): AWS formatting not used by function
            context (dictionary): AWS formatting not used by function

    Returns:
            [type]: [description]
    """

    """
	Get the agency information.
	"""
    agency_values = json.loads(get_all_agencies())
    for agency in agency_values["results"]:
        timeout = agency["attributes"]["CEIEVPTimeoutSecs"]
        print(f'Agency {agency["name"]} - {timeout}')
        agency_id = agency["name"]
        site_name = agency["parentPath"].replace("/", "")
        vehicle_results = get_agency_assets(site_name, agency_id)

        if vehicle_results is not None:
            for veh in vehicle_results:
                veh = json.loads(veh)
                if veh["attributes"].get("CEIDeviceID", None) is None:
                    continue
                if veh["templateId"] != "ceicom":
                    print(f'Processing {veh["attributes"]["CEIDeviceID"]}')
                    print(
                        f'{veh["attributes"]["CEIDeviceID"]} last referenced: {veh["attributes"].get("CEILastReferenced")}'
                    )
                    try:
                        try:
                            last_called = float(veh["attributes"]["CEILastReferenced"])
                        except:
                            last_called = 0.0
                        elapsed_seconds = round((time.time() - last_called))
                        if elapsed_seconds > timeout:
                            gttSerialNum = None
                            if "gttSerial" in veh["attributes"]:
                                gttSerialNum = veh["attributes"]["gttSerial"]

                            else:
                                gttSerialNum = get_gtt_serial(
                                    veh["attributes"]["CEIDeviceID"], agency_id
                                )

                            print(
                                f'{veh["attributes"]["CEIDeviceID"]} gtt Serial# - {gttSerialNum}'
                            )

                            if gttSerialNum is not None:
                                activate_vehicle(
                                    site_name,
                                    agency_id,
                                    veh["attributes"]["CEIDeviceID"],
                                    gttSerialNum,
                                    "None",
                                    False,
                                )

                                veh["attributes"][
                                    "CEILastReferenced"
                                ] = f"{time.time()}"
                                veh["attributes"]["CEIVehicleActive"] = False
                                record_entry(
                                    agency_id,
                                    json.dumps(veh),
                                    veh["attributes"]["CEIDeviceID"],
                                )

                                post_log(
                                    site_name,
                                    agency_id,
                                    veh["attributes"]["CEIDeviceID"],
                                    "None",
                                    "Info",
                                    "Timeout Operation",
                                    "CEI EVP Timeout",
                                    "Vehicle has timed out",
                                )
                    except Exception as e:
                        post_log(
                            site_name,
                            agency_id,
                            veh["attributes"]["CEIDeviceID"],
                            "None",
                            "Error",
                            "Processing Exception",
                            "CEI EVP Timeout",
                            e,
                        )
                        logging.error(f"ERROR {e}")
                        raise e
