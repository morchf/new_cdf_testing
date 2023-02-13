#!/usr/bin/env python
import boto3
import os
import json
from iot_core import register_thing, remove_thing
from status import (
    DEVICE_STATUS_EXISTS,
    DEVICE_STATUS_DOES_NOT_EXIST,
    DEVICE_STATUS_NO_CERT_IN_ASSET_LIB,
    DEVICE_STATUS_NO_DEVICE_IN_ASSET_LIB,
    DEVICE_STATUS_NO_CERT_IN_IOT_CORE,
)
from asset_lib import (
    agency_read,
    device_create,
    device_read,
    device_write,
    device_delete,
    communicator_associate,
)

from aws_cert_auth import new_dev, del_dev, get_cert_id

log = True


def get_json(name):
    file_name = f"/tmp/{name}.json"
    if os.path.exists(file_name):
        f = open(file_name, "r")
        json_object = json.load(f)
        f.close()
    return json_object


def check_content(rc_input, read_communicator_content):
    rc = False
    if rc_input >= 200 and rc_input < 300:
        if read_communicator_content:
            try:
                json.loads(read_communicator_content)
                rc = True
            except Exception as e:
                if log:
                    print(e)
                    print(
                        f"check_content - rc_input = {rc}, "
                        f"read_communicator_content = {read_communicator_content}"
                    )
                pass
        elif log:
            print(
                f"check_content - rc_input = {rc}, "
                f"read_communicator_content= {read_communicator_content}"
            )
    elif log:
        print(
            f"check_content - rc_input = {rc}, "
            f"read_communicator_content= {read_communicator_content}"
        )
    return rc


class Communicator:
    def __init__(self, region_name, agency_name, vehicle_name, communicator_name):
        self.region_name = region_name
        self.agency_name = agency_name
        self.vehicle_name = vehicle_name
        self.communicator_name = communicator_name
        self.name_2100 = "2100"
        self.cert_2100_name = f"{self.agency_name.upper()}_{self.name_2100}"
        self.iot = boto3.client("iot")
        self.s3 = boto3.client("s3")
        self.name = f"{self.agency_name}_{self.communicator_name}"
        self.refresh()

    def create(self, communicator_json):
        prefix = (
            self.region_name.upper()
            + "/AGENCIES/"
            + self.agency_name.upper()
            + "/DEVICES"
        )
        if log:
            print(f"****** Communicator create = {self.communicator_name} *****")
        self.refresh()
        if self.status == DEVICE_STATUS_DOES_NOT_EXIST:
            self.http_code, self.http_content = device_create(communicator_json)
            self.refresh()
        if self.status == DEVICE_STATUS_NO_DEVICE_IN_ASSET_LIB:
            self.asso_code, self.asso_content = communicator_associate(
                self.communicator_name, self.vehicle_name
            )
            self.refresh()
        if self.status == DEVICE_STATUS_NO_CERT_IN_ASSET_LIB:

            communicator_json = get_json(self.communicator_name)
            if communicator_json["attributes"]["model"] == "MP-70":
                rc = new_dev(self.region_name, self.agency_name, self.communicator_name)
                if rc:
                    devCertId = get_cert_id(self.name, prefix)
                    write_cert_id_json = (
                        f'{{ "attributes": {{ "devCertId": "{devCertId}" }} }} '
                    )
                    self.write(write_cert_id_json)
                    register_thing(self.name, devCertId)
            # if model is 2100/2101, need to get cert2100Id from its agency name
            elif communicator_json["attributes"]["model"] in ["2100", "2101"]:
                agency_status, agency_content = agency_read(
                    self.region_name, self.agency_name
                )
                print(agency_content)
                if agency_status == 200:
                    print("if agency_status == 200:")
                    agency_json = json.loads(agency_content)
                    Cert2100Id = agency_json["attributes"]["Cert2100Id"]
                    print(Cert2100Id)
                    write_cert_id_json = (
                        f'{{ "attributes": {{ "devCertId": "{Cert2100Id}" }} }} '
                    )
                    self.write(write_cert_id_json)
            self.refresh()

    def delete(self):
        prefix = (
            self.region_name.upper()
            + "/AGENCIES/"
            + self.agency_name.upper()
            + "/DEVICES"
        )
        if log:
            print(f"****** Communicator delete = {self.communicator_name} *****")
        self.refresh()
        if self.status != DEVICE_STATUS_DOES_NOT_EXIST:
            self.http_response, self.http_content = device_delete(
                self.communicator_name
            )
            self.refresh()
        if self.status == DEVICE_STATUS_DOES_NOT_EXIST:
            devCertId = get_cert_id(self.name, prefix)
            print("devCertId is: " + devCertId)
            if devCertId:
                remove_thing(self.name, devCertId)
                del_dev(self.region_name, self.agency_name, self.communicator_name)
            self.refresh()

    def write(self, write_json):
        if log:
            print(f"****** Communicator write = {self.communicator_name} *****")
        self.refresh()
        if self.status != DEVICE_STATUS_DOES_NOT_EXIST:
            self.http_response, self.http_content = device_write(
                self.communicator_name, write_json
            )
            self.refresh()

    """
        Refresh communicator json and status.  Refresh() is effectively a read function
        because the json is updated with latest values.

        If something goes wrong with the Agency() in which the communicator is or will
        be a member of, then errors are propagated up.

        If communicator does not exist in asset lib then json is None and
        status is DEVICE_STATUS_DOES_NOT_EXIST.

        If communicator does exist in asset lib, then verification of communicator
        cert and cert policy are performend. Both communicator cert and policy
        are in IoT Core.
    """

    def refresh(self):
        if log:
            print(f"****** Communicator refresh = {self.communicator_name} *****")

        rc, read_communicator_content = device_read(self.communicator_name)
        if not check_content(rc, read_communicator_content):
            if log:
                print(
                    f"HTTP Error, rc = {rc},"
                    f" read_communicator_content = {read_communicator_content}"
                )
            self.status = DEVICE_STATUS_DOES_NOT_EXIST
            return

        communicator_content_json_obj = json.loads(read_communicator_content)
        communicator_attributes_json_obj = communicator_content_json_obj.get(
            "attributes", None
        )
        if not communicator_attributes_json_obj:
            if log:
                print(
                    f"HTTP response no attributes. communicator_attributes_json_obj"
                    f" = {communicator_attributes_json_obj}"
                )
            self.status = DEVICE_STATUS_DOES_NOT_EXIST
            return

        communicator_devices_json_obj = communicator_content_json_obj.get(
            "devices", None
        )
        if not communicator_devices_json_obj:
            if log:
                print(
                    f"HTTP response no devices. communicator_devices_json_obj"
                    f" = {communicator_devices_json_obj}"
                )
            if self.vehicle_name:
                self.status = DEVICE_STATUS_NO_DEVICE_IN_ASSET_LIB
                return

        # Communicator of 'communicator_name' exists
        devCertId = communicator_attributes_json_obj.get("devCertId", "NULL_CERT")
        if devCertId == "NULL_CERT":
            if log:
                print(
                    f"HTTP response no dev_cert_id. devCertId = {devCertId}. "
                    f"communicator_attributes_json_obj = "
                    f"{communicator_attributes_json_obj}"
                )
            self.status = DEVICE_STATUS_NO_CERT_IN_ASSET_LIB
            return

        try:
            # Exception thrown if cert id not registered in IoT Core
            self.iot.describe_certificate(certificateId=devCertId)
            cert_present = True
        except Exception as e:
            if log:
                print(f"Dev cert id not in IoT Core. devCertId = {devCertId}")
                print(f"Exception = {str(e)}")
            cert_present = False
        if cert_present:
            self.status = DEVICE_STATUS_EXISTS
        else:
            self.status = DEVICE_STATUS_NO_CERT_IN_IOT_CORE
