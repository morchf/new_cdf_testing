#!/usr/bin/env python

import boto3
import json
from status import (
    REGION_STATUS_EXISTS,
    REGION_STATUS_DOES_NOT_EXIST,
    REGION_STATUS_NO_CA_IN_ASSET_LIB,
    REGION_STATUS_NO_CA_IN_IOT_CORE,
)
from asset_lib import (
    region_create,
    region_read,
    region_write,
    region_delete,
)
from aws_cert_auth import new_root_ca, del_root_ca, get_cert_id

log = True


def check_content(rc_input, region_content_json_obj):
    rc = False
    if type(region_content_json_obj) == dict:
        if region_content_json_obj.get("attributes", None):
            if rc_input >= 200 and rc_input < 300:
                rc = True
            elif log:
                print(
                    f"check_content - rc_input = {rc}, region_content_json_obj = {region_content_json_obj}"
                )
        elif log:
            print(
                f"check_content - rc_input = {rc}, region_content_json_obj = {region_content_json_obj}"
            )
    elif log:
        print(
            f"check_content - rc_input = {rc}, region_content_json_obj = {region_content_json_obj}"
        )
    return rc


"""
Class for an region: create, delete, write, refresh.

All functions interfaced with asset library, IOT Core, and KMS.
"""


class Region:
    def __init__(self, region_name):
        self.region_name = region_name
        self.name = f"{self.region_name.upper()}_ROOTCA"
        self.iot = boto3.client("iot")
        self.s3 = boto3.client("s3")
        self.refresh()

    def create(self, region_json):
        if log:
            print(f"****** Region create = {self.region_name} *****")
        self.refresh()
        if self.status == REGION_STATUS_DOES_NOT_EXIST:
            self.http_code, self.http_content = region_create(
                self.region_name, region_json
            )
            self.refresh()
        if self.status == REGION_STATUS_NO_CA_IN_ASSET_LIB:
            rc = new_root_ca(self.region_name)
            if rc:
                caCertId = get_cert_id(self.name, self.region_name.upper())
                write_cert_id_json = (
                    f'{{ "attributes": {{ "caCertId": "{caCertId}" }} }}'
                )
                self.write(write_cert_id_json)
            self.refresh()

    def delete(self):
        if log:
            print(f"****** Region delete = {self.region_name} *****")
        self.refresh()
        if self.status != REGION_STATUS_DOES_NOT_EXIST:
            self.http_response, self.http_content = region_delete(self.region_name)
            self.refresh()
        if self.status == REGION_STATUS_DOES_NOT_EXIST:
            del_root_ca(self.region_name)
            self.refresh()

    def write(self, write_json):
        if log:
            print(f"****** Region write = {self.region_name} *****")
        self.refresh()
        if self.status != REGION_STATUS_DOES_NOT_EXIST:
            self.http_response, self.http_content = region_write(
                self.region_name, write_json
            )
            self.refresh()

    """
        Refresh region json and status.  Refresh() is effectively a read function because
        the json is updated with latest values.

        If agency does not exist in asset lib then json is None and
        status is REGION_STATUS_DOES_NOT_EXIST.

        If agency does exist in asset lib, then verification of CA and private key are performed.
    """

    def refresh(self):
        if log:
            print(f"****** Region refresh = {self.region_name} *****")

        rc, read_region_content = region_read(self.region_name)
        region_content_json_obj = json.loads(read_region_content)

        if check_content(rc, region_content_json_obj):
            region_attributes_json_obj = region_content_json_obj.get("attributes", None)

            if region_attributes_json_obj:
                # Region of 'region_name' exists
                caCertId = region_attributes_json_obj.get("caCertId", "NULL_CA")

                if caCertId != "NULL_CA":
                    # self-signed CA cert id is written in asset lib
                    try:
                        # Exception thrown if cert id not registered in IoT Core
                        self.iot.describe_ca_certificate(certificateId=caCertId)
                        ca_present = True
                    except Exception as e:
                        if log:
                            print(f"Cert id not in IoT Core. caCertId = {caCertId}")
                            print(f"Exception = {str(e)}")
                        ca_present = False
                    if ca_present == True:
                        self.status = REGION_STATUS_EXISTS
                    else:
                        self.status = REGION_STATUS_NO_CA_IN_IOT_CORE

                else:
                    if log:
                        print(
                            f"HTTP response no caCertId. caCertId = {caCertId}. region_attributes_json_obj = {region_attributes_json_obj}"
                        )
                    self.status = REGION_STATUS_NO_CA_IN_ASSET_LIB

            else:
                if log:
                    print(
                        f"HTTP response no attributes. region_attributes_json_obj = {region_attributes_json_obj}"
                    )
                self.status = REGION_STATUS_DOES_NOT_EXIST

        else:
            if log:
                print(
                    f"HTTP Error, rc = {rc}, region_content_json_obj = {region_content_json_obj}"
                )
            self.status = REGION_STATUS_DOES_NOT_EXIST
